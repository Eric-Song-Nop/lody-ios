package app.innei.lody.kit.runtime

import android.annotation.SuppressLint
import android.content.Context
import android.os.Handler
import android.os.Looper
import android.webkit.JavascriptInterface
import android.webkit.ConsoleMessage
import android.webkit.WebChromeClient
import android.webkit.RenderProcessGoneDetail
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger

/** One owner, one local bundled runtime. All WebView operations run on main. */
@SuppressLint("SetJavaScriptEnabled")
internal class DataRuntime(
  context: Context,
  private val onEvent: (JSONObject) -> Unit,
  private val onFailure: (String) -> Unit,
  private val intercept: ((WebResourceRequest) -> WebResourceResponse)? = null,
) {
  companion object {
    const val ORIGIN = "https://appassets.androidplatform.net"
    const val MAX_CHARS = 4 * 1024 * 1024
    const val CHUNK_CHARS = 32 * 1024
  }

  private val main = Handler(Looper.getMainLooper())
  private val alive = AtomicBoolean(true)
  private val failed = AtomicBoolean(false)
  private val queuedChars = AtomicInteger(0)
  private val queuedMessages = AtomicInteger(0)
  private val pending = mutableMapOf<Int, (Result<Any?>) -> Unit>()
  private var nextRequest = 0
  private var ready = false
  private val view: WebView
  @Volatile var receivedChunks = 0
    private set
  @Volatile var peakQueuedChars = 0
    private set
  private val startupDeadline = Runnable { fail("startup_timeout") }

  init {
    check(Looper.myLooper() == Looper.getMainLooper())
    view = WebView(context)
    view.settings.apply {
      javaScriptEnabled = true
      allowFileAccess = false
      allowContentAccess = false
      domStorageEnabled = false
      javaScriptCanOpenWindowsAutomatically = false
      mixedContentMode = android.webkit.WebSettings.MIXED_CONTENT_NEVER_ALLOW
    }
    view.addJavascriptInterface(Bridge(), "lodyDataHost")
    view.webChromeClient = object : WebChromeClient() {
      override fun onConsoleMessage(message: ConsoleMessage): Boolean {
        if (message.messageLevel() == ConsoleMessage.MessageLevel.ERROR) fail("javascript_error_line_${message.lineNumber()}")
        return true
      }
    }
    view.webViewClient = object : WebViewClient() {
      override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest) = true
      override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse? {
        if (request.url.toString() == "$ORIGIN/runtime.html" && request.method == "GET") {
          return WebResourceResponse("text/html", "utf-8", context.assets.open("lody-runtime/DataRuntime.html"))
        }
        return intercept?.invoke(request)
      }

      override fun onPageFinished(view: WebView, url: String) {
        if (alive.get() && !failed.get()) onEvent(JSONObject().put("type", "hostPageLoaded"))
      }

      override fun onReceivedError(view: WebView, request: WebResourceRequest, error: WebResourceError) {
        if (request.isForMainFrame) fail("page_load_failed")
      }

      override fun onRenderProcessGone(view: WebView, detail: RenderProcessGoneDetail): Boolean {
        fail("renderer_gone")
        return true
      }
    }
    main.postDelayed(startupDeadline, 30_000)
    view.loadUrl("$ORIGIN/runtime.html")
  }

  fun invoke(method: String, args: JSONArray = JSONArray(), completion: (Result<Any?>) -> Unit = {}) {
    check(Looper.myLooper() == Looper.getMainLooper())
    if (!alive.get() || !ready) {
      completion(Result.failure(IllegalStateException("runtime_not_ready")))
      return
    }
    val id = ++nextRequest
    val script = "globalThis.lodyRuntimeInvoke($id,${JSONObject.quote(method)},$args)"
    if (script.length > 64 * 1024 || pending.size >= 16) {
      completion(Result.failure(IllegalStateException("command_limit")))
      return
    }
    pending[id] = completion
    main.postDelayed({
      pending.remove(id)?.invoke(Result.failure(IllegalStateException("command_timeout")))
    }, 30_000)
    view.evaluateJavascript(script, null)
  }

  fun close() {
    check(Looper.myLooper() == Looper.getMainLooper())
    if (!alive.getAndSet(false)) return
    main.removeCallbacksAndMessages(null)
    val completions = pending.values.toList()
    pending.clear()
    view.stopLoading()
    view.removeJavascriptInterface("lodyDataHost")
    view.destroy()
    completions.forEach { it(Result.failure(IllegalStateException("runtime_stopped"))) }
  }

  private fun fail(reason: String) {
    if (!alive.get() || !failed.compareAndSet(false, true)) return
    main.post {
      if (alive.get()) {
        close()
        onFailure(reason)
      }
    }
  }

  private fun receive(value: String) {
    // A fatal bridge error can precede already-admitted messages on main.
    // Fence them immediately, before the asynchronous WebView teardown runs.
    if (!alive.get() || failed.get()) return
    val event = try { JSONObject(value) } catch (_: Exception) {
      fail("invalid_host_message")
      return
    }
    when (event.optString("type")) {
      "bridgeError" -> fail("bridge_limit")
      "ready" -> {
        ready = true
        main.removeCallbacks(startupDeadline)
        onEvent(event)
      }
      "rpc" -> {
        val callback = pending.remove(event.optInt("id")) ?: return
        if (event.has("error")) callback(Result.failure(IllegalStateException("runtime_command_failed")))
        else callback(Result.success(event.opt("result").takeUnless { it === JSONObject.NULL }))
      }
      else -> onEvent(event)
    }
  }

  // Android invokes this object on its bridge thread. Admission is synchronous;
  // bounded events cross to main only after the final ordered chunk arrives.
  private inner class Bridge {
    private var messageId = -1
    private var nextChunk = 0
    private var chunkCount = 0
    private var buffer = StringBuilder()

    @JavascriptInterface
    @Synchronized
    fun postChunk(id: Int, index: Int, total: Int, value: String): Boolean {
      if (!alive.get() || failed.get()) return false
      if (value.length > CHUNK_CHARS || total !in 1..128) return reject()
      if (index == 0) {
        if (nextChunk != 0) return reject()
        messageId = id
        chunkCount = total
      }
      if (id != messageId || index != nextChunk || total != chunkCount) return reject()
      if (buffer.length + value.length > MAX_CHARS) return reject()
      buffer.append(value)
      receivedChunks++
      nextChunk++
      if (nextChunk != total) return true
      val message = buffer.toString()
      buffer = StringBuilder()
      nextChunk = 0
      val admitted = queuedChars.addAndGet(message.length)
      if (admitted > MAX_CHARS || queuedMessages.incrementAndGet() > 16) return reject()
      peakQueuedChars = maxOf(peakQueuedChars, admitted)
      main.post {
        queuedChars.addAndGet(-message.length)
        queuedMessages.decrementAndGet()
        receive(message)
      }
      return true
    }

    private fun reject(): Boolean {
      buffer = StringBuilder()
      fail("bridge_limit")
      return false
    }
  }
}
