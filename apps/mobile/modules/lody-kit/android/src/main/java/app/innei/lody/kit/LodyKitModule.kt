package app.innei.lody.kit

import android.os.Build
import android.os.Handler
import android.os.Looper
import app.innei.lody.kit.runtime.RuntimeRecoveryVerification
import app.innei.lody.kit.runtime.DataRuntimeVerification
import expo.modules.kotlin.Promise
import java.io.File
import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition

class LodyKitModule : Module() {
  private var recovery: RuntimeRecoveryVerification? = null
  private var observing = false
  private var verification: DataRuntimeVerification? = null

  override fun definition() = ModuleDefinition {
    Name("LodyKit")
    Constants {
      mapOf("runtimeInfo" to mapOf(
        "moduleName" to "LodyKit",
        "systemVersion" to "Android ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})"
      ))
    }
    Events("onAppActive", "onRecoveryPhase")
    AsyncFunction("runDataRuntimeVerification") { promise: Promise ->
      Handler(Looper.getMainLooper()).post {
        val context = appContext.reactContext
        if (context == null || verification != null || recovery != null) {
          promise.reject("runtime_unavailable", "Runtime verification is unavailable or already running", null)
        } else {
          try {
            val probe = DataRuntimeVerification(context)
            verification = probe
            probe.run { result ->
              verification = null
              result.fold({ report ->
                try {
                  val output = context.getExternalFilesDir(null) ?: error("evidence_storage_unavailable")
                  File(output, "lody-runtime-verification.json").writeText(report)
                  promise.resolve(report)
                } catch (error: Exception) { promise.reject("evidence_write_failed", "Could not save verification evidence", error) }
              }, { promise.reject("runtime_verification_failed", it.message, it) })
            }
          } catch (error: Exception) {
            verification = null
            promise.reject("runtime_verification_failed", "Could not start runtime verification", error)
          }
        }
      }
    }
    AsyncFunction("runRuntimeRecoveryVerification") { promise: Promise ->
      Handler(Looper.getMainLooper()).post {
        val context = appContext.reactContext
        if (context == null || verification != null || recovery != null) {
          promise.reject("runtime_unavailable", "Runtime verification is unavailable or already running", null)
        } else {
          try {
            val probe = RuntimeRecoveryVerification(context) { phase ->
              sendEvent("onRecoveryPhase", mapOf("phase" to phase))
            }
            recovery = probe
            probe.run { result ->
              recovery = null
              result.fold({ report ->
                try {
                  val output = context.getExternalFilesDir(null) ?: error("evidence_storage_unavailable")
                  File(output, "lody-recovery-verification.json").writeText(report)
                  promise.resolve(report)
                } catch (error: Exception) { promise.reject("evidence_write_failed", "Could not save recovery evidence", error) }
              }, { promise.reject("recovery_verification_failed", it.message, it) })
            }
          } catch (error: Exception) {
            recovery?.close()
            recovery = null
            promise.reject("recovery_verification_failed", "Could not start recovery verification", error)
          }
        }
      }
    }
    OnActivityEntersBackground {
      Handler(Looper.getMainLooper()).post { recovery?.enterBackground() }
    }
    OnStartObserving { observing = true }
    OnStopObserving { observing = false }
    OnActivityEntersForeground {
      Handler(Looper.getMainLooper()).post { recovery?.enterForeground() }
      if (observing) sendEvent("onAppActive", emptyMap<String, Any>())
    }
    OnDestroy {
      observing = false
      Handler(Looper.getMainLooper()).post {
        recovery?.close()
        recovery = null
        verification?.close()
        verification = null
      }
    }
  }
}
