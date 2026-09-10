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
  private val inboxPreferences by lazy {
    app.innei.lody.kit.preferences.InboxPreferences(requireNotNull(appContext.reactContext))
  }
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
    View(app.innei.lody.kit.chrome.LodySymbolView::class) {
      Prop("symbol") { view: app.innei.lody.kit.chrome.LodySymbolView, value: String -> view.setSymbol(value) }
      Prop("pointSize") { view: app.innei.lody.kit.chrome.LodySymbolView, value: Float -> view.setPointSize(value) }
      Prop("tint") { view: app.innei.lody.kit.chrome.LodySymbolView, value: String? -> view.setTint(value) }
    }
    View(app.innei.lody.kit.chrome.LodySymbolButton::class) {
      Events("onSymbolPress", "onSymbolLongPress")
      Prop("symbol") { view: app.innei.lody.kit.chrome.LodySymbolButton, value: String -> view.setSymbol(value) }
      Prop("accessibilityName") { view: app.innei.lody.kit.chrome.LodySymbolButton, value: String -> view.setLabel(value) }
      Prop("disabled") { view: app.innei.lody.kit.chrome.LodySymbolButton, value: Boolean -> view.setDisabled(value) }
      Prop("prominent") { view: app.innei.lody.kit.chrome.LodySymbolButton, value: Boolean -> view.setProminent(value) }
      Prop("longPress") { view: app.innei.lody.kit.chrome.LodySymbolButton, value: Boolean -> view.setLongPress(value) }
      Prop("tint") { view: app.innei.lody.kit.chrome.LodySymbolButton, value: String? -> view.setTint(value) }
    }
    View(app.innei.lody.kit.press.LodyPressable::class) {
      Events("onNativePress")
      Prop("disabled") { view: app.innei.lody.kit.press.LodyPressable, value: Boolean -> view.setDisabled(value) }
      Prop("haptic") { view: app.innei.lody.kit.press.LodyPressable, value: Boolean -> view.haptic = value }
      Prop("pressScale") { view: app.innei.lody.kit.press.LodyPressable, value: Float ->
        require(value.isFinite() && value > 0 && value <= 1) { "Press scale must be between 0 and 1" }
        view.pressScale = value
      }
    }
    View(app.innei.lody.kit.press.LodyGlassSurface::class) {
      Prop("radius") { view: app.innei.lody.kit.press.LodyGlassSurface, value: Float -> view.setRadius(value) }
      Prop("tint") { view: app.innei.lody.kit.press.LodyGlassSurface, value: String? -> view.setTint(value) }
    }
    View(app.innei.lody.kit.chrome.LodyMenuButton::class) {
      Events("onSelect", "onSize")
      Prop("label") { view: app.innei.lody.kit.chrome.LodyMenuButton, value: String -> view.setLabel(value) }
      Prop("accessibilityName") { view: app.innei.lody.kit.chrome.LodyMenuButton, value: String -> view.setAccessibilityName(value) }
      Prop("avatar") { view: app.innei.lody.kit.chrome.LodyMenuButton, value: app.innei.lody.kit.chrome.LodyMenuAvatar -> view.setAvatar(value) }
      Prop("items") { view: app.innei.lody.kit.chrome.LodyMenuButton, value: List<app.innei.lody.kit.menu.LodyMenuEntry> -> view.setItems(value) }
    }
    View(app.innei.lody.kit.menu.LodyContextMenu::class) {
      Events("onAction")
      Prop("actions") { view: app.innei.lody.kit.menu.LodyContextMenu, value: List<app.innei.lody.kit.menu.LodyMenuEntry> -> view.setActions(value) }
    }
    View(app.innei.lody.kit.list.LodyGroupedList::class) {
      Events("onRowPress", "onRefresh")
      Prop("sections") { view: app.innei.lody.kit.list.LodyGroupedList, value: List<app.innei.lody.kit.list.LodyListSection> -> view.setSections(value) }
      Prop("placeholder") { view: app.innei.lody.kit.list.LodyGroupedList, value: String -> view.setPlaceholder(value) }
      Prop("transparent") { view: app.innei.lody.kit.list.LodyGroupedList, value: Boolean -> view.setTransparent(value) }
      Prop("accent") { view: app.innei.lody.kit.list.LodyGroupedList, value: String? -> view.setAccent(value) }
      Prop("bottomInset") { view: app.innei.lody.kit.list.LodyGroupedList, value: Float -> view.setBottomInset(value) }
      Prop("refreshEnabled") { view: app.innei.lody.kit.list.LodyGroupedList, value: Boolean -> view.setRefreshEnabled(value) }
      Prop("refreshing") { view: app.innei.lody.kit.list.LodyGroupedList, value: Boolean -> view.setRefreshing(value) }
    }
    View(app.innei.lody.kit.chrome.LodyCloseButton::class) {
      Events("onClose")
      Prop("label") { view: app.innei.lody.kit.chrome.LodyCloseButton, label: String? -> view.setLabel(label) }
    }
    AsyncFunction("runLocaleVerification") {
      val context = requireNotNull(appContext.reactContext) { "Locale context unavailable" }
      app.innei.lody.kit.locale.LocaleVerification.run(context)
    }
    Function("saveInboxView") { index: Int -> inboxPreferences.saveView(index) }
    Function("readInboxExpansion") { inboxPreferences.readExpansion() }
    Function("saveInboxExpansion") { projectId: String, expanded: Boolean -> inboxPreferences.saveExpansion(projectId, expanded) }
    Function("copyText") { text: String ->
      val context = requireNotNull(appContext.reactContext) { "Clipboard context unavailable" }
      val clipboard = requireNotNull(context.getSystemService(android.content.ClipboardManager::class.java))
      clipboard.setPrimaryClip(android.content.ClipData.newPlainText("", text))
    }
    AsyncFunction("selectionFeedback") {
      val activity = requireNotNull(appContext.currentActivity) { "Haptic activity unavailable" }
      activity.window.decorView.performHapticFeedback(android.view.HapticFeedbackConstants.CLOCK_TICK)
      Unit
    }.runOnQueue(expo.modules.kotlin.functions.Queues.MAIN)
    Constants {
      mapOf("initialInboxView" to inboxPreferences.initialView(), "runtimeInfo" to mapOf(
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
