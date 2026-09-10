package app.innei.lody.kit.runtime

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import org.json.JSONArray
import org.json.JSONObject
import kotlin.coroutines.Continuation
import kotlin.coroutines.EmptyCoroutineContext
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException
import kotlin.coroutines.startCoroutine
import kotlin.coroutines.suspendCoroutine

/** Real WebViews and renderer termination; synthetic time controls only watchdog deadlines. */
internal class RuntimeRecoveryVerification(private val context: Context, private val onPhase: (String) -> Unit) {
  private val main = Handler(Looper.getMainLooper())
  private val fixture = DataRuntimeVerification(context)
  private val views = mutableMapOf<Int, DataRuntime>()
  private val events = mutableMapOf<Int, (JSONObject) -> Unit>()
  private val failures = mutableMapOf<Int, (String) -> Unit>()
  private val commands = JSONArray()
  private val states = JSONArray()
  private val checks = JSONArray()
  private var now = 0L
  private var suppressReady = true
  private var suppressPing = false
  private var backgroundSeen = false
  private var foregroundSeen = false
  private var awaitingLifecycle = false
  private var readySeen = 0
  private var pingReplies = 0
  private val readGenerations = mutableSetOf<Int>()
  private var catalogEvents = 0
  private var deliveredEvents = 0
  private var completion: ((Result<String>) -> Unit)? = null
  private var waiting: Continuation<Unit>? = null
  private lateinit var supervisor: RuntimeSupervisor

  fun run(done: (Result<String>) -> Unit) {
    completion = done
    supervisor = RuntimeSupervisor(
      workspaceId = "fixture-workspace",
      factory = { generation, receive, failed ->
        events[generation] = receive
        failures[generation] = failed
        val runtime = DataRuntime(context,
          onEvent = { event ->
            if (event.optString("type") == "ready") readySeen++
            if (!(suppressReady && event.optString("type") == "ready")) receive(event)
          },
          onFailure = failed,
          intercept = fixture.interceptor("increment"))
        views[generation] = runtime
        object : RuntimeEndpoint {
          override fun invoke(method: String, args: JSONArray, completion: (Result<Any?>) -> Unit) {
            commands.put(JSONObject().put("generation", generation).put("method", method))
            runtime.invoke(method, args) reply@{ result ->
              if (method == "ping") {
                pingReplies++
                if (suppressPing) return@reply
              }
              completion(result)
            }
          }
          override fun suspend() = runtime.suspend()
          override fun resume() = runtime.resume()
          override fun close() = runtime.close()
        }
      },
      grant = { resolve -> resolve(JSONObject().put("token", "offline-fixture-only").put("gatewayBaseUrl", DataRuntime.ORIGIN).put("expiresIn", 3600)) },
      onEvent = { event ->
        deliveredEvents++
        if (event.optString("type") == "catalog") catalogEvents++
        if (event.optString("type") == "session" && event.optBoolean("synced")) {
          val session = JSONObject(event.getString("session"))
          check(session.getJSONArray("entries").length() == 1 && session.toString().contains("Real Loro WASM 回复"))
          readGenerations.add(supervisor.health.generation)
        }
      },
      onState = { state, generation, reason ->
        states.put(JSONObject().put("state", state.name).put("generation", generation).put("reason", reason ?: JSONObject.NULL).put("clock", now))
      },
      clock = { now },
      automaticTicks = false,
    )
    val scenario: suspend () -> Unit = { exercise() }
    scenario.startCoroutine(object : Continuation<Unit> {
      override val context = EmptyCoroutineContext
      override fun resumeWith(result: Result<Unit>) = finish(result)
    })
  }

  fun enterBackground() {
    if (!::supervisor.isInitialized) return
    supervisor.suspend()
    if (awaitingLifecycle) {
      backgroundSeen = true
      now += 1_000_000
      supervisor.tick()
    }
  }

  fun enterForeground() {
    if (!::supervisor.isInitialized) return
    supervisor.resume()
    if (awaitingLifecycle && backgroundSeen) foregroundSeen = true
  }

  fun close() {
    val pending = waiting
    waiting = null
    if (::supervisor.isInitialized) supervisor.stop()
    pending?.resumeWithException(IllegalStateException("verification_cancelled"))
    finish(Result.failure(IllegalStateException("verification_cancelled")))
  }

  private fun finish(result: Result<Unit>) {
    val callback = completion ?: return
    completion = null
    main.removeCallbacksAndMessages(null)
    supervisor.stop()
    callback(result.map {
      JSONObject().put("fixtureVersion", "recovery-v1").put("runtimeSha256", fixture.runtimeHash)
        .put("cases", checks).put("states", states).put("commands", commands)
        .put("createdViews", views.size).put("closedViews", views.values.count { it.isClosed })
        .put("httpWrites", fixture.writeCount).put("readGenerations", JSONArray(readGenerations.toList())).toString()
    })
  }

  private suspend fun exercise() {
    supervisor.watchSessions(listOf("s1"), "s1")
    supervisor.start()
    val first = supervisor.health.generation
    waitFor("real_page_ready") { readySeen == 1 }
    check(supervisor.health.state == RuntimeHealth.State.STARTING)
    now = 20_000
    supervisor.tick()
    check(supervisor.health.reason == "startup_timeout" && views.getValue(first).isClosed)
    pass("A-REC-01", "Native deadline closed a real page whose ready callback was withheld")
    suppressReady = false
    now += 1_000
    supervisor.tick()
    waitFor("read_recovery") { supervisor.health.state == RuntimeHealth.State.READY && catalogEvents > 0 && supervisor.health.generation in readGenerations }
    val recovered = supervisor.health.generation
    val eventCount = deliveredEvents
    events.getValue(first)(JSONObject().put("type", "catalog").put("catalog", "old-instance"))
    failures.getValue(first)("renderer_gone")
    check(deliveredEvents == eventCount && supervisor.health.generation == recovered && supervisor.health.state == RuntimeHealth.State.READY)
    pass("A-REC-04", "Old event and failure callbacks cannot mutate the replacement owner")

    val pingsBefore = pingReplies
    awaitingLifecycle = true
    onPhase("Recovery background ready")
    waitFor("system_background") { backgroundSeen }
    check(supervisor.health.generation == recovered && supervisor.health.state == RuntimeHealth.State.SUSPENDED)
    waitFor("system_foreground") { foregroundSeen && pingReplies > pingsBefore }
    awaitingLifecycle = false
    check(supervisor.health.state == RuntimeHealth.State.READY && supervisor.health.generation == recovered)
    onPhase("Recovery running")
    pass("A-REC-02", "Background time does not restart the retained view; a real foreground ping succeeds")

    val notSent = command("sendTurn", JSONArray().put(JSONObject().put("sessionId", "missing-session").put("text", "offline recovery probe"))) as JSONObject
    check(notSent.getString("state") == "not_sent")
    val beforeDropped = pingReplies
    suppressPing = true
    now += 2_000
    supervisor.tick()
    waitFor("dropped_ping") { pingReplies > beforeDropped }
    now += 8_000
    supervisor.tick()
    check(supervisor.health.reason == "heartbeat_timeout")
    suppressPing = false
    now += 2_000
    supervisor.tick()
    waitFor("heartbeat_recovery") { supervisor.health.state == RuntimeHealth.State.READY && supervisor.health.generation in readGenerations }

    check(views.getValue(supervisor.health.generation).terminateRendererForVerification()) { "renderer_termination_unavailable" }
    waitFor("renderer_gone") { supervisor.health.state == RuntimeHealth.State.FAILED }
    check(supervisor.health.reason == "renderer_gone")
    now += 4_000
    supervisor.tick()
    waitFor("renderer_recovery") { supervisor.health.state == RuntimeHealth.State.READY && supervisor.health.generation in readGenerations }
    check(views.getValue(supervisor.health.generation).terminateRendererForVerification())
    waitFor("restart_exhausted") { supervisor.health.reason == "restart_limit" }
    val exhausted = supervisor.health.generation
    now += 60_000
    supervisor.tick()
    check(supervisor.health.generation == exhausted && supervisor.health.state == RuntimeHealth.State.FAILED)
    check(supervisor.health.automaticRestarts == 3 && views.values.all { it.isClosed })
    pass("A-REC-03", "Heartbeat loss and real renderer termination recover finitely, then stop at three automatic restarts")

    supervisor.start()
    waitFor("manual_recovery") { supervisor.health.state == RuntimeHealth.State.READY && supervisor.health.generation in readGenerations }
    val last = supervisor.health.generation
    supervisor.stop()
    val stoppedEvents = deliveredEvents
    events.getValue(last)(JSONObject().put("type", "catalog").put("catalog", "after-stop"))
    now += 9_000_000
    supervisor.tick()
    check(deliveredEvents == stoppedEvents && supervisor.health.state == RuntimeHealth.State.STOPPED)
    check(views.values.all { it.isClosed } && fixture.writeCount == 0)
    check((0 until commands.length()).count { commands.getJSONObject(it).getString("method") == "sendTurn" } == 1)
    pass("A-REC-05", "Stop closes all owners, suppresses events, and never replays the one issued command")
  }

  private suspend fun command(method: String, args: JSONArray): Any? = suspendCoroutine { continuation ->
    supervisor.command(method, args) { continuation.resumeWith(it) }
  }

  private suspend fun waitFor(label: String, condition: () -> Boolean) = suspendCoroutine<Unit> { continuation ->
    waiting = continuation
    val deadline = SystemClock.elapsedRealtime() + 30_000
    val poll = object : Runnable {
      override fun run() {
        if (waiting !== continuation) return
        try {
          if (condition()) {
            waiting = null
            continuation.resume(Unit)
          } else if (SystemClock.elapsedRealtime() >= deadline) {
            waiting = null
            continuation.resumeWithException(IllegalStateException("timeout_$label:${supervisor.health.state}:${supervisor.health.reason}"))
          } else main.postDelayed(this, 50)
        } catch (error: Exception) {
          waiting = null
          continuation.resumeWithException(error)
        }
      }
    }
    main.post(poll)
  }

  private fun pass(id: String, detail: String) {
    checks.put(JSONObject().put("id", id).put("status", "pass").put("detail", detail))
  }
}
