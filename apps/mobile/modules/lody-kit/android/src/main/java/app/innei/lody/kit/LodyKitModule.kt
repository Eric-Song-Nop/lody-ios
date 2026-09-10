package app.innei.lody.kit

import app.innei.lody.kit.storage.AuthCredentials
import app.innei.lody.kit.storage.LocalStore
import app.innei.lody.kit.storage.StorageVerification
import java.util.concurrent.Executors
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
  private val storageWorker = Executors.newSingleThreadExecutor { task -> Thread(task, "LodyStorage") }
  @Volatile private var localStore: LocalStore? = null
  private var authCredentials: AuthCredentials? = null
  private var destroyed = false

  private fun storageOperation(promise: Promise, clearContext: Boolean = false, action: (LocalStore, AuthCredentials, android.content.Context, Long) -> Any?) {
    Handler(Looper.getMainLooper()).post {
      val context = appContext.reactContext
      if (context == null || destroyed) {
        promise.reject("storage_unavailable", "Storage is unavailable", null)
        return@post
      }
      if (clearContext) {
        recovery?.close()
        verification?.close()
        localStore?.invalidate()
      }
      val generation = localStore?.generation ?: 0L
      storageWorker.execute {
        try {
          val store = localStore ?: LocalStore(context).also { localStore = it }
          val credentials = authCredentials ?: AuthCredentials(context).also { authCredentials = it }
          promise.resolve(action(store, credentials, context, generation))
        } catch (error: Exception) {
          val allowed = setOf("credential_reauthorization_required", "storage_context_replaced", "storage_value_limit")
          val code = error.message?.takeIf { it in allowed } ?: "storage_failed"
          promise.reject(code, code, null)
        }
      }
    }
  }

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
    AsyncFunction("readAuthToken") { promise: Promise ->
      storageOperation(promise) { _, auth, _, _ -> auth.read() }
    }
    AsyncFunction("saveAuthToken") { token: String, promise: Promise ->
      storageOperation(promise) { _, auth, _, _ -> auth.save(token); null }
    }
    AsyncFunction("clearAuthToken") { promise: Promise ->
      storageOperation(promise, clearContext = true) { store, auth, _, _ -> auth.clear(); store.clear(); null }
    }
    AsyncFunction("readLocalStartup") { promise: Promise ->
      storageOperation(promise) { store, _, _, _ -> store.startup() }
    }
    AsyncFunction("readLocalValue") { key: String, promise: Promise ->
      storageOperation(promise) { store, _, _, _ -> store.read(key) }
    }
    AsyncFunction("writeLocalValue") { key: String, value: String, promise: Promise ->
      storageOperation(promise) { store, _, _, generation -> store.write(key, value, generation); null }
    }
    AsyncFunction("clearLocalValues") { promise: Promise ->
      storageOperation(promise, clearContext = true) { store, _, _, _ -> store.clear(); null }
    }
    AsyncFunction("runStorageVerification") { seedCatalog: String?, promise: Promise ->
      storageOperation(promise) { _, _, context, _ ->
        val report = StorageVerification(context).run(seedCatalog)
        val output = context.getExternalFilesDir(null) ?: error("evidence_storage_unavailable")
        File(output, "lody-storage-verification.json").writeText(report)
        report
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
        destroyed = true
        storageWorker.execute { localStore?.close() }
        storageWorker.shutdown()
        recovery?.close()
        recovery = null
        verification?.close()
        verification = null
      }
    }
  }
}
