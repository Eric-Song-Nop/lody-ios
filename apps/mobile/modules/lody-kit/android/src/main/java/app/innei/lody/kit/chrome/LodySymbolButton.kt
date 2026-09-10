package app.innei.lody.kit.chrome

import android.content.Context
import android.content.res.ColorStateList
import android.content.res.Configuration
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.RippleDrawable
import android.widget.ImageButton
import expo.modules.kotlin.AppContext
import expo.modules.kotlin.views.ExpoView
import expo.modules.kotlin.viewevent.EventDispatcher

class LodySymbolButton(context: Context, appContext: AppContext) : ExpoView(context, appContext) {
  override val shouldUseAndroidLayout = true
  val onSymbolPress by EventDispatcher()
  val onSymbolLongPress by EventDispatcher()
  private val button = ImageButton(context)
  private var tint: String? = null
  private var prominent = false

  init {
    minimumWidth = LodyUiColors.dp(context, 48f)
    minimumHeight = minimumWidth
    button.minimumWidth = minimumWidth
    button.minimumHeight = minimumHeight
    val padding = LodyUiColors.dp(context, 12f)
    button.setPadding(padding, padding, padding, padding)
    button.scaleType = android.widget.ImageView.ScaleType.FIT_CENTER
    button.setOnClickListener { onSymbolPress(emptyMap<String, Any>()) }
    addView(button, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT))
    updateColors()
  }

  fun setSymbol(value: String) { button.setImageResource(LodySymbols.resource(value)) }
  fun setLabel(value: String) { button.contentDescription = value }
  fun setDisabled(value: Boolean) { button.isEnabled = !value; button.alpha = if (value) 0.38f else 1f }
  fun setTint(value: String?) { tint = value; updateColors() }
  fun setProminent(value: Boolean) { prominent = value; updateColors() }
  fun setLongPress(value: Boolean) {
    if (value) {
      button.setOnLongClickListener { onSymbolLongPress(emptyMap<String, Any>()); true }
    } else {
      button.setOnLongClickListener(null)
      button.isLongClickable = false
    }
  }
  private fun updateColors() {
    val color = tint?.takeIf { it.isNotBlank() }?.let(android.graphics.Color::parseColor) ?: LodyUiColors.action(context)
    button.imageTintList = ColorStateList.valueOf(color)
    val mask = GradientDrawable().apply { shape = GradientDrawable.OVAL; setColor(android.graphics.Color.WHITE) }
    val fill = if (prominent) GradientDrawable().apply { shape = GradientDrawable.OVAL; setColor(LodyUiColors.actionSurface(context)) } else null
    button.background = RippleDrawable(ColorStateList.valueOf((color and 0x00ffffff) or 0x33000000), fill, mask)
  }
  override fun onConfigurationChanged(configuration: Configuration) {
    super.onConfigurationChanged(configuration)
    updateColors()
  }
}
