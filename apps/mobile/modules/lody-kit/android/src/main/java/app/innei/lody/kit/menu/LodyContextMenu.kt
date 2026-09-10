package app.innei.lody.kit.menu

import android.content.Context
import android.content.res.Configuration
import android.view.GestureDetector
import android.view.MotionEvent
import android.view.View
import expo.modules.kotlin.AppContext
import expo.modules.kotlin.views.ExpoView
import expo.modules.kotlin.viewevent.EventDispatcher

class LodyContextMenu(context: Context, appContext: AppContext) : ExpoView(context, appContext) {
  val onAction by EventDispatcher()
  private val menu = LodyPopupMenu(this) { onAction(mapOf("id" to it)) }
  private var consumedLongPress = false
  private val detector = GestureDetector(context, object : GestureDetector.SimpleOnGestureListener() {
    override fun onDown(event: MotionEvent) = true
    override fun onLongPress(event: MotionEvent) {
      if (performLongClick()) {
        consumedLongPress = true
        cancelChildTouch(event)
      }
    }
  })

  init {
    isFocusable = true
    importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_YES
    setOnLongClickListener { menu.show() }
  }

  fun setActions(value: List<LodyMenuEntry>) {
    menu.setEntries(value)
    isLongClickable = value.isNotEmpty()
  }

  private fun cancelChildTouch(event: MotionEvent) {
    val cancel = MotionEvent.obtain(event)
    cancel.action = MotionEvent.ACTION_CANCEL
    super.dispatchTouchEvent(cancel)
    cancel.recycle()
  }

  override fun dispatchTouchEvent(event: MotionEvent): Boolean {
    if (event.actionMasked == MotionEvent.ACTION_DOWN) consumedLongPress = false
    detector.onTouchEvent(event)
    if (consumedLongPress) return true
    // Observe the gesture without intercepting ordinary child taps or scrolling.
    return super.dispatchTouchEvent(event)
  }

  override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
    setMeasuredDimension(MeasureSpec.getSize(widthMeasureSpec), MeasureSpec.getSize(heightMeasureSpec))
  }
  override fun onLayout(changed: Boolean, left: Int, top: Int, right: Int, bottom: Int) = Unit
  override fun onDetachedFromWindow() { menu.dismiss(); super.onDetachedFromWindow() }
  override fun onVisibilityChanged(changedView: View, visibility: Int) {
    super.onVisibilityChanged(changedView, visibility)
    if (!isShown) menu.dismiss()
  }
  override fun onWindowVisibilityChanged(visibility: Int) {
    super.onWindowVisibilityChanged(visibility)
    if (visibility != View.VISIBLE) menu.dismiss()
  }
  override fun onConfigurationChanged(configuration: Configuration) {
    super.onConfigurationChanged(configuration)
    menu.dismiss()
  }
}
