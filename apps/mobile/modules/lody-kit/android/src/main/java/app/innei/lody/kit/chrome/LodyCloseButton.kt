package app.innei.lody.kit.chrome

import android.content.Context
import android.content.res.ColorStateList
import android.util.TypedValue
import android.widget.ImageButton
import expo.modules.kotlin.AppContext
import expo.modules.kotlin.views.ExpoView
import expo.modules.kotlin.viewevent.EventDispatcher

class LodyCloseButton(context: Context, appContext: AppContext) : ExpoView(context, appContext) {
  override val shouldUseAndroidLayout = true
  val onClose by EventDispatcher()
  private val button = ImageButton(context)

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
    val colors = context.obtainStyledAttributes(intArrayOf(android.R.attr.textColorPrimary))
    button.imageTintList = colors.getColorStateList(0) ?: ColorStateList.valueOf(android.graphics.Color.DKGRAY)
    colors.recycle()
    button.setOnClickListener { onClose(emptyMap<String, Any>()) }
    addView(button, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT))
  }

  fun setLabel(label: String?) { button.contentDescription = label }
}
