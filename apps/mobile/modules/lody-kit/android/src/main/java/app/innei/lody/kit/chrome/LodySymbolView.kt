package app.innei.lody.kit.chrome

import android.content.Context
import android.content.res.Configuration
import android.content.res.ColorStateList
import android.view.Gravity
import android.widget.ImageView
import expo.modules.kotlin.AppContext
import expo.modules.kotlin.views.ExpoView

class LodySymbolView(context: Context, appContext: AppContext) : ExpoView(context, appContext) {
  override val shouldUseAndroidLayout = true
  private val image = ImageView(context)
  private var tint: String? = null

  init {
    gravity = Gravity.CENTER
    importantForAccessibility = IMPORTANT_FOR_ACCESSIBILITY_NO
    image.importantForAccessibility = IMPORTANT_FOR_ACCESSIBILITY_NO
    addView(image)
    setPointSize(20f)
    setTint(null)
  }

  fun setSymbol(symbol: String) { image.setImageResource(LodySymbols.resource(symbol)) }
  fun setPointSize(size: Float) {
    require(size.isFinite() && size > 0) { "Symbol size must be positive" }
    val pixels = LodyUiColors.dp(context, size)
    image.layoutParams = LayoutParams(pixels, pixels)
  }
  fun setTint(value: String?) {
    tint = value
    image.imageTintList = ColorStateList.valueOf(LodyUiColors.tint(context, value))
  }
  override fun onConfigurationChanged(configuration: Configuration) {
    super.onConfigurationChanged(configuration)
    setTint(tint)
  }
}
