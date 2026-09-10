package app.innei.lody.kit.chrome

import app.innei.lody.kit.locale.LodyStrings
import android.content.Context
import android.content.res.ColorStateList
import android.content.res.Configuration
import android.util.TypedValue
import android.widget.ImageButton
import expo.modules.kotlin.AppContext
import expo.modules.kotlin.views.ExpoView
import expo.modules.kotlin.viewevent.EventDispatcher

class LodyCloseButton(context: Context, appContext: AppContext) : ExpoView(context, appContext) {
  override val shouldUseAndroidLayout = true
  val onClose by EventDispatcher()
  private val button = ImageButton(context)
  private var explicitLabel: String? = null

  init {
    val size = (48 * resources.displayMetrics.density).toInt()
    minimumWidth = size
    minimumHeight = size
    button.minimumWidth = size
    button.minimumHeight = size
    button.setImageResource(android.R.drawable.ic_menu_close_clear_cancel)
    val ripple = TypedValue()
    context.theme.resolveAttribute(android.R.attr.selectableItemBackgroundBorderless, ripple, true)
    button.setBackgroundResource(ripple.resourceId)
    updateColors()
    updateLabel()
    button.setOnClickListener { onClose(emptyMap<String, Any>()) }
    addView(button, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT))
  }

  fun setLabel(label: String?) { explicitLabel = label; updateLabel() }
  private fun updateLabel() { button.contentDescription = explicitLabel ?: LodyStrings.text(context, "native.close") }
  private fun updateColors() {
    button.imageTintList = ColorStateList.valueOf(LodyUiColors.text(context))
  }
  override fun onConfigurationChanged(configuration: Configuration) {
    super.onConfigurationChanged(configuration)
    updateColors()
    updateLabel()
  }
}
