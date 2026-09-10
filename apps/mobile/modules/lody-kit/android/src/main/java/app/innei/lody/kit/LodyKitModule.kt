package app.innei.lody.kit

import android.os.Build
import android.os.Handler
import android.os.Looper
import app.innei.lody.kit.runtime.DataRuntimeVerification
import expo.modules.kotlin.Promise
import java.io.File
import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition

class LodyKitModule : Module() {
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
    Events("onAppActive")
    AsyncFunction("runDataRuntimeVerification") { promise: Promise ->
      Handler(Looper.getMainLooper()).post {
        val context = appContext.reactContext
        if (context == null || verification != null) {
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
    OnStartObserving { observing = true }
    OnStopObserving { observing = false }
    OnActivityEntersForeground {
      if (observing) sendEvent("onAppActive", emptyMap<String, Any>())
    }
    OnDestroy {
      observing = false
      Handler(Looper.getMainLooper()).post {
        verification?.close()
        verification = null
      }
    }
  }
}
