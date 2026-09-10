package app.innei.lody.kit.runtime

/** Monotonic-clock policy, independent of WebView and Android scheduling. */
internal class RuntimeHealth {
  enum class State { STOPPED, STARTING, READY, SUSPENDED, FAILED }
  var state = State.STOPPED
    private set
  var generation = 0
    private set
  var automaticRestarts = 0
    private set
  var reason: String? = null
    private set
  private var foreground = true
  private var acknowledged = false
  private var deadline = 0L
  private var restartAt: Long? = null

  fun start(now: Long) {
    automaticRestarts = 0
    begin(now)
  }

  fun begin(now: Long) {
    generation++
    acknowledged = false
    reason = null
    restartAt = null
    deadline = now + 20_000
    state = if (foreground) State.STARTING else State.SUSPENDED
  }

  fun accepts(value: Int) = value == generation && state in setOf(State.STARTING, State.READY, State.SUSPENDED)

  fun acknowledge(value: Int, now: Long): Boolean {
    if (!accepts(value)) return false
    acknowledged = true
    deadline = now + 8_000
    if (foreground) state = State.READY
    return true
  }

  fun suspend() {
    foreground = false
    if (state == State.STARTING || state == State.READY) state = State.SUSPENDED
  }

  fun resume(now: Long) {
    foreground = true
    if (state == State.SUSPENDED) {
      state = if (acknowledged) State.READY else State.STARTING
      deadline = now + if (acknowledged) 8_000 else 20_000
    }
  }

  fun timeoutReason(now: Long): String? {
    if (!foreground || now < deadline) return null
    return when (state) {
      State.STARTING -> "startup_timeout"
      State.READY -> "heartbeat_timeout"
      else -> null
    }
  }

  fun fail(value: Int, failure: String, now: Long): Boolean {
    if (!accepts(value)) return false
    state = State.FAILED
    reason = failure
    if (automaticRestarts < 3) {
      restartAt = now + (1_000L shl automaticRestarts)
      automaticRestarts++
    } else {
      restartAt = null
      reason = "restart_limit"
    }
    return true
  }

  fun restartDue(now: Long) = foreground && state == State.FAILED && restartAt?.let { now >= it } == true

  fun stop() {
    generation++
    state = State.STOPPED
    restartAt = null
    reason = null
  }
}
