package app.innei.lody.kit.runtime

import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import org.json.JSONArray
import org.json.JSONObject

/** Restarts subscriptions only. Commands are never retained for replay. */
internal class RuntimeSupervisor(
  private val workspaceId: String,
  private val factory: (Int, (JSONObject) -> Unit, (String) -> Unit) -> RuntimeEndpoint,
  private val grant: ((JSONObject?) -> Unit) -> Unit,
  private val onEvent: (JSONObject) -> Unit,
  private val onState: (RuntimeHealth.State, Int, String?) -> Unit,
  private val clock: () -> Long = SystemClock::elapsedRealtime,
  private val automaticTicks: Boolean = true,
) {
  val health = RuntimeHealth()
  private val main = Handler(Looper.getMainLooper())
  private var endpoint: RuntimeEndpoint? = null
  private var pingPending = false
  private var nextPing = 0L
  private var sessions = emptyList<String>()
  private var currentSession: String? = null
  private val timer = object : Runnable {
    override fun run() {
      tick()
      if (health.state != RuntimeHealth.State.STOPPED && automaticTicks) main.postDelayed(this, 500)
    }
  }

  fun start() {
    assertMain()
    closeEndpoint()
    health.start(clock())
    open()
    main.removeCallbacks(timer)
    if (automaticTicks) main.postDelayed(timer, 500)
  }

  fun suspend() {
    assertMain()
    health.suspend()
    endpoint?.suspend()
    publishState()
  }

  fun resume() {
    assertMain()
    health.resume(clock())
    endpoint?.resume()
    nextPing = clock()
    publishState()
    tick()
  }

  fun stop() {
    assertMain()
    health.stop()
    main.removeCallbacksAndMessages(null)
    closeEndpoint()
    sessions = emptyList()
    currentSession = null
    publishState()
  }

  fun watchSessions(ids: List<String>, current: String?) {
    assertMain()
    require(ids.size <= 4 && (current == null || current in ids))
    sessions = ids.distinct()
    currentSession = current
    if (health.state == RuntimeHealth.State.READY) restoreSessions()
  }

  fun command(method: String, args: JSONArray, completion: (Result<Any?>) -> Unit) {
    assertMain()
    val active = endpoint
    if (active == null || health.state != RuntimeHealth.State.READY) {
      completion(Result.failure(IllegalStateException("runtime_not_ready")))
      return
    }
    active.invoke(method, args, completion)
  }

  fun tick() {
    assertMain()
    val now = clock()
    health.timeoutReason(now)?.let { failed(health.generation, it) }
    if (health.restartDue(now)) {
      health.begin(now)
      open()
    }
    if (health.state != RuntimeHealth.State.READY || pingPending || now < nextPing) return
    val generation = health.generation
    val active = endpoint ?: return
    pingPending = true
    nextPing = now + 2_000
    active.invoke("ping") { result ->
      if (!health.accepts(generation) || endpoint !== active) return@invoke
      pingPending = false
      if (result.getOrNull() == true) health.acknowledge(generation, clock())
    }
  }

  private fun open() {
    val generation = health.generation
    pingPending = false
    nextPing = clock() + 2_000
    publishState()
    try {
      endpoint = factory(generation, { event -> receive(generation, event) }, { reason -> failed(generation, reason) })
      if (health.state == RuntimeHealth.State.SUSPENDED) endpoint?.suspend()
    } catch (_: Exception) {
      failed(generation, "runtime_creation_failed")
    }
  }

  private fun receive(generation: Int, event: JSONObject) {
    if (!health.accepts(generation)) return
    when (event.optString("type")) {
      "ready" -> {
        health.acknowledge(generation, clock())
        publishState()
        endpoint?.invoke("start", JSONArray().put(workspaceId))
        restoreSessions()
      }
      "grant" -> grant { value ->
        main.post {
          if (health.accepts(generation)) endpoint?.invoke("grant", JSONArray().put(value ?: JSONObject.NULL))
        }
      }
      else -> onEvent(event)
    }
  }

  private fun restoreSessions() {
    if (sessions.isNotEmpty()) endpoint?.invoke("restoreSessions", JSONArray().put(JSONArray(sessions)).put(currentSession ?: JSONObject.NULL))
  }

  private fun failed(generation: Int, reason: String) {
    if (!health.fail(generation, reason, clock())) return
    closeEndpoint()
    publishState()
  }

  private fun closeEndpoint() {
    val old = endpoint
    endpoint = null
    pingPending = false
    old?.close()
  }

  private fun publishState() = onState(health.state, health.generation, health.reason)
  private fun assertMain() = check(Looper.myLooper() == Looper.getMainLooper())
}
