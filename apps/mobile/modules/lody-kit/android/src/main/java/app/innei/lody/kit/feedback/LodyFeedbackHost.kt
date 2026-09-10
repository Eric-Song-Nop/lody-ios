package app.innei.lody.kit.feedback

import android.content.Context
import android.content.res.Configuration
import app.innei.lody.kit.LodyKitModule
import expo.modules.kotlin.AppContext
import expo.modules.kotlin.views.ExpoView

/** Registers the real window containing this page; it draws no React overlay. */
class LodyFeedbackHost(context: Context, appContext: AppContext) : ExpoView(context, appContext) {
  private val owner get() = (appContext.registry.getModule("LodyKit") as? LodyKitModule)?.feedback

  init {
    importantForAccessibility = IMPORTANT_FOR_ACCESSIBILITY_NO
    isClickable = false
    isFocusable = false
  }

  override fun onAttachedToWindow() {
    super.onAttachedToWindow()
    owner?.register(this)
  }

  override fun onDetachedFromWindow() {
    owner?.unregister(this)
    super.onDetachedFromWindow()
  }

  override fun onWindowFocusChanged(hasWindowFocus: Boolean) {
    super.onWindowFocusChanged(hasWindowFocus)
    owner?.refreshHost()
  }

  override fun onConfigurationChanged(newConfig: Configuration) {
    super.onConfigurationChanged(newConfig)
    owner?.refreshHost(rebuild = true)
  }

  override fun onLayout(changed: Boolean, left: Int, top: Int, right: Int, bottom: Int) {
    super.onLayout(changed, left, top, right, bottom)
    if (changed) owner?.refreshHost()
  }
}
