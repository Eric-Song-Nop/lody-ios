package app.innei.lody.kit.press

import android.content.Context
import android.util.TypedValue
import android.view.HapticFeedbackConstants
import expo.modules.kotlin.AppContext
import expo.modules.kotlin.views.ExpoView
import expo.modules.kotlin.viewevent.EventDispatcher

class LodyPressable(context: Context, appContext: AppContext) : ExpoView(context, appContext) {
  val onNativePress by EventDispatcher()
  var haptic = true
  var pressScale = 0.985f

  init {
    val ripple = TypedValue()
    context.theme.resolveAttribute(android.R.attr.selectableItemBackground, ripple, true)
    foreground = context.getDrawable(ripple.resourceId)
    isClickable = true
    isFocusable = true
    setOnClickListener {
      if (haptic) performHapticFeedback(HapticFeedbackConstants.VIRTUAL_KEY)
      onNativePress(emptyMap<String, Any>())
    }
  }
  fun setDisabled(value: Boolean) {
    isEnabled = !value
    alpha = if (value) 0.38f else 1f
    if (value) isPressed = false
  }
  override fun performClick(): Boolean = isEnabled && super.performClick()
  override fun setPressed(pressed: Boolean) {
    super.setPressed(pressed)
    val scale = if (pressed && isEnabled) pressScale else 1f
    animate().scaleX(scale).scaleY(scale).setDuration(100).start()
  }
  override fun onDetachedFromWindow() {
    animate().cancel()
    scaleX = 1f
    scaleY = 1f
    super.onDetachedFromWindow()
  }
}
