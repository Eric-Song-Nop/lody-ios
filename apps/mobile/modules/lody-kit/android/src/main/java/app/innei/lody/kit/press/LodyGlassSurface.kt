package app.innei.lody.kit.press

import android.content.Context
import android.content.res.Configuration
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import app.innei.lody.kit.chrome.LodyUiColors
import expo.modules.kotlin.AppContext
import expo.modules.kotlin.views.ExpoView

/** Android counterpart of the glass facade: an opaque, neutral Material surface. */
class LodyGlassSurface(context: Context, appContext: AppContext) : ExpoView(context, appContext) {
  private var radius = 14f
  private var tint: String? = null
  init {
    importantForAccessibility = IMPORTANT_FOR_ACCESSIBILITY_NO
    isClickable = false
    updateSurface()
  }
  fun setRadius(value: Float) { require(value.isFinite() && value >= 0); radius = value; updateSurface() }
  fun setTint(value: String?) { tint = value; updateSurface() }
  private fun updateSurface() {
    background = GradientDrawable().apply {
      cornerRadius = radius * resources.displayMetrics.density
      setColor(tint?.takeIf { it.isNotBlank() }?.let(Color::parseColor) ?: LodyUiColors.surface(context))
    }
  }
  override fun onConfigurationChanged(configuration: Configuration) {
    super.onConfigurationChanged(configuration)
    updateSurface()
  }
}
