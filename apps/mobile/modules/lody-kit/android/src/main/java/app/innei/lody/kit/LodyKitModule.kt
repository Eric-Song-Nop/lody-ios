package app.innei.lody.kit

import android.os.Build
import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition

class LodyKitModule : Module() {
  private var observing = false

  override fun definition() = ModuleDefinition {
    Name("LodyKit")
    Constants {
      mapOf("runtimeInfo" to mapOf(
        "moduleName" to "LodyKit",
        "systemVersion" to "Android ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})"
      ))
    }
    Events("onAppActive")
    OnStartObserving { observing = true }
    OnStopObserving { observing = false }
    OnActivityEntersForeground {
      if (observing) sendEvent("onAppActive", emptyMap<String, Any>())
    }
    OnDestroy { observing = false }
  }
}
