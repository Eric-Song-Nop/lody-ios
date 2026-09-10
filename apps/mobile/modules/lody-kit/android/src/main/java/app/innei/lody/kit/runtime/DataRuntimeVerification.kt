package app.innei.lody.kit.runtime

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayInputStream
import java.io.FilterInputStream
import java.util.concurrent.atomic.AtomicInteger

/** Deterministic HTTP boundary only: the bundled runtime and WASM are unchanged. */
internal class DataRuntimeVerification(private val context: Context) {
  private val main = Handler(Looper.getMainLooper())
  private val manifest = context.assets.open("lody-runtime/verification/manifest.json")
    .bufferedReader().use { JSONObject(it.readText()) }
  private var runtime: DataRuntime? = null
  private var completion: ((Result<String>) -> Unit)? = null
  private val reports = JSONArray()
  private var index = -1
  private var projections = 0
  private var historySeen = false
  private val reads = AtomicInteger(0)
  private val writes = AtomicInteger(0)
  private var projectionChars = 0
  private var lastEvent = "none"

  fun run(done: (Result<String>) -> Unit) {
    check(completion == null)
    completion = done
    next()
  }

  fun close() {
    main.removeCallbacksAndMessages(null)
    runtime?.close()
    runtime = null
    val callback = completion
    completion = null
    callback?.invoke(Result.failure(IllegalStateException("verification_cancelled")))
  }

  private fun fail(reason: String) {
    val callback = completion ?: return
    completion = null
    main.removeCallbacksAndMessages(null)
    runtime?.close()
    runtime = null
    callback(Result.failure(IllegalStateException("case_$index:$reason:event=$lastEvent:reads=${reads.get()}:projections=$projections")))
  }

  private fun next() {
    runtime?.close()
    runtime = null
    main.removeCallbacksAndMessages(null)
    index++
    val cases = manifest.getJSONArray("cases")
    if (index == cases.length()) {
      val callback = completion
      completion = null
      callback?.invoke(Result.success(JSONObject()
        .put("fixtureVersion", manifest.getString("version"))
        .put("runtimeSha256", manifest.getString("runtimeSha256"))
        .put("assetHashes", manifest.getJSONObject("assets"))
        .put("cases", reports).toString()))
      return
    }
    projections = 0
    lastEvent = "none"
    historySeen = false
    projectionChars = 0
    reads.set(0)
    writes.set(0)
    val current = index
    val fixture = cases.getJSONObject(index)
    main.postDelayed({ if (index == current) fail("deadline") }, 30_000)
    runtime = DataRuntime(context,
      onEvent = { event ->
        if (index == current && completion != null) {
          try { receive(fixture, event) } catch (_: Exception) { fail("invalid_projection_shape") }
        }
      },
      onFailure = { reason ->
        if (index == current) {
          if (fixture.optString("hostError") == reason && projections == 0) pass(fixture)
          else fail(reason)
        }
      },
      intercept = { request -> response(fixture, request) },
    )
  }

  private fun receive(fixture: JSONObject, event: JSONObject) {
    lastEvent = event.optString("type").take(40)
    when (event.optString("type")) {
      "ready" -> runtime?.invoke("start", JSONArray().put("fixture-workspace"))
      "grant" -> runtime?.invoke("grant", JSONArray().put(JSONObject()
        .put("token", "offline-fixture-only")
        .put("gatewayBaseUrl", DataRuntime.ORIGIN)
        .put("expiresIn", 3600)))
      "catalog" -> {
        if (fixture.has("error") || fixture.has("hostError")) { fail("invalid_input_published_catalog"); return }
        val expected = fixture.getJSONArray("expected")
        if (projections >= expected.length()) { fail("unexpected_projection"); return }
        val value = event.getString("catalog")
        if (normalized(JSONObject(value)) != normalized(expected.getJSONObject(projections))) {
          fail("projection_mismatch"); return
        }
        projectionChars += value.length
        projections++
      }
      "synced" -> {
        if (fixture.has("error") || fixture.has("hostError")) { fail("invalid_input_reported_live"); return }
        if (projections != fixture.getJSONArray("expected").length()) return
        if (fixture.getString("name") == "increment") {
          if (!historySeen) runtime?.invoke("session", JSONArray().put("s1"))
        } else pass(fixture)
      }
      "session" -> {
        if (!event.optBoolean("synced")) return
        val session = JSONObject(event.getString("session"))
        val entries = session.getJSONArray("entries")
        if (entries.length() != 1 || entries.getJSONObject(0).getString("id") != "reply" ||
          !entries.getJSONObject(0).getBoolean("finished") ||
          !session.toString().contains("Real Loro WASM 回复")) {
          fail("loro_projection_mismatch"); return
        }
        historySeen = true
        pass(fixture)
      }
      "syncError" -> {
        if (!fixture.has("error") || event.optString("reason") != fixture.getString("error") || projections != 0) {
          fail("unexpected_sync_error"); return
        }
        pass(fixture)
      }
    }
  }

  private fun pass(fixture: JSONObject) {
    if (writes.get() != 0) { fail("unexpected_write"); return }
    val chunks = runtime?.receivedChunks ?: 0
    if (fixture.getString("name") == "large" && (projectionChars <= DataRuntime.CHUNK_CHARS || chunks < 2)) {
      fail("large_projection_not_exercised"); return
    }
    reports.put(JSONObject().put("name", fixture.getString("name"))
      .put("status", "pass").put("projections", projections).put("projectionChars", projectionChars)
      .put("chunks", chunks).put("peakQueuedChars", runtime?.peakQueuedChars)
      .put("httpReads", reads.get()).put("httpWrites", writes.get()).put("loroHistory", historySeen))
    runtime?.close()
    runtime = null
    main.removeCallbacksAndMessages(null)
    main.post { next() }
  }

  private fun response(fixture: JSONObject, request: WebResourceRequest): WebResourceResponse {
    if (request.method != "GET") writes.incrementAndGet()
    val headers = mutableMapOf("Stream-Next-Offset" to "2", "Stream-Up-To-Date" to "true", "Cache-Control" to "no-store")
    val path = request.url.path.orEmpty()
    val history = path.contains(":s:")
    var asset: String? = null
    var status = 200
    var mime = "application/octet-stream"
    if (request.url.scheme != "https" || request.url.host != "appassets.androidplatform.net" || !path.startsWith("/ds/lody/") || request.method != "GET") {
      status = 404
    } else {
      reads.incrementAndGet()
      if (path.endsWith("/bootstrap")) {
        asset = if (history) manifest.getString("history") else fixture.getString("bootstrap")
        mime = "multipart/mixed"
        headers["Content-Type"] = "multipart/mixed; boundary=lody-fixture"
        headers["Stream-Snapshot-Offset"] = "1"
        headers["Stream-Next-Offset"] = "1"
      } else if (!history && fixture.has("update") && request.url.getQueryParameter("offset") == "1") {
        asset = fixture.getString("update")
        headers["Content-Type"] = mime
      } else status = 204
    }
    val stream = if (asset == null) ByteArrayInputStream(byteArrayOf())
      else context.assets.open("lody-runtime/verification/$asset")
    // Force fragmented native reads; no replacement StreamsClient or decoder.
    val fragmented = object : FilterInputStream(stream) {
      override fun read(bytes: ByteArray, offset: Int, count: Int): Int = super.read(bytes, offset, minOf(count, 997))
    }
    return WebResourceResponse(mime, null, status, if (status == 200) "OK" else "Empty", headers, fragmented)
  }

  private fun normalized(value: Any?): Any? = when (value) {
    null, JSONObject.NULL -> null
    is JSONObject -> value.keys().asSequence().sorted().associateWith { normalized(value.get(it)) }
    is JSONArray -> (0 until value.length()).map { normalized(value.get(it)) }
    is Number -> value.toDouble()
    else -> value
  }
}
