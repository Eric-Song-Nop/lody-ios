package app.innei.lody.kit.chrome

import android.content.Context
import android.content.res.ColorStateList
import android.content.res.Configuration
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.ColorFilter
import android.graphics.Paint
import android.graphics.PixelFormat
import android.graphics.drawable.Drawable
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.RippleDrawable
import android.view.View
import android.widget.Button
import app.innei.lody.kit.menu.LodyMenuEntry
import app.innei.lody.kit.menu.LodyPopupMenu
import expo.modules.kotlin.AppContext
import expo.modules.kotlin.records.Field
import expo.modules.kotlin.records.Record
import expo.modules.kotlin.views.ExpoView
import expo.modules.kotlin.viewevent.EventDispatcher

class LodyMenuAvatar : Record {
  @Field var text: String = ""
  @Field var color: String = "#1565C0"
}

class LodyMenuButton(context: Context, appContext: AppContext) : ExpoView(context, appContext) {
  override val shouldUseAndroidLayout = true
  val onSelect by EventDispatcher()
  val onSize by EventDispatcher()
  private val button = Button(context)
  private val menu = LodyPopupMenu(button) { onSelect(mapOf("id" to it)) }
  private var avatar = LodyMenuAvatar()
  private var reportedWidth = -1

  init {
    val minimum = LodyUiColors.dp(context, 48f)
    minimumWidth = minimum
    minimumHeight = minimum
    button.minWidth = minimum
    button.minHeight = minimum
    button.isAllCaps = false
    button.maxLines = 1
    button.ellipsize = android.text.TextUtils.TruncateAt.END
    button.setPadding(LodyUiColors.dp(context, 12f), 0, LodyUiColors.dp(context, 12f), 0)
    button.compoundDrawablePadding = LodyUiColors.dp(context, 8f)
    button.setOnClickListener { menu.show() }
    addView(button, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT))
    updateColors()
  }

  fun setItems(value: List<LodyMenuEntry>) {
    menu.setEntries(value)
    button.isEnabled = value.isNotEmpty()
    button.alpha = if (value.isEmpty()) 0.38f else 1f
  }
  fun setLabel(value: String) { button.text = value; reportSize() }
  fun setAccessibilityName(value: String) { button.contentDescription = value }
  fun setAvatar(value: LodyMenuAvatar) { Color.parseColor(value.color); avatar = value; updateColors() }

  private fun updateColors() {
    button.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, 16f)
    button.setTextColor(LodyUiColors.text(context))
    val fill = GradientDrawable().apply {
      cornerRadius = LodyUiColors.dp(context, 12f).toFloat()
      setColor(LodyUiColors.surface(context))
    }
    val mask = GradientDrawable().apply { cornerRadius = LodyUiColors.dp(context, 12f).toFloat(); setColor(Color.WHITE) }
    button.background = RippleDrawable(ColorStateList.valueOf((LodyUiColors.action(context) and 0x00ffffff) or 0x33000000), fill, mask)
    val icon = AvatarDrawable(avatar.text, Color.parseColor(avatar.color), LodyUiColors.dp(context, 28f))
    icon.setBounds(0, 0, icon.intrinsicWidth, icon.intrinsicHeight)
    button.setCompoundDrawablesRelative(icon, null, null, null)
    reportSize()
  }

  private fun reportSize() {
    post {
      if (!isAttachedToWindow) return@post
      button.measure(MeasureSpec.UNSPECIFIED, MeasureSpec.UNSPECIFIED)
      val width = minOf(200, kotlin.math.ceil(button.measuredWidth / context.resources.displayMetrics.density.toDouble()).toInt())
      if (width != reportedWidth) { reportedWidth = width; onSize(mapOf("width" to width)) }
      requestLayout()
    }
  }
  override fun onAttachedToWindow() { super.onAttachedToWindow(); reportSize() }
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
    updateColors()
  }
}

private class AvatarDrawable(private val text: String, private val color: Int, private val size: Int) : Drawable() {
  private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
  override fun getIntrinsicWidth() = size
  override fun getIntrinsicHeight() = size
  override fun draw(canvas: Canvas) {
    val centerX = bounds.exactCenterX()
    val centerY = bounds.exactCenterY()
    paint.color = color
    canvas.drawCircle(centerX, centerY, bounds.width() / 2f, paint)
    val luminance = Color.luminance(color)
    paint.color = if (luminance > 0.4) Color.BLACK else Color.WHITE
    paint.textAlign = Paint.Align.CENTER
    paint.textSize = size * 0.48f
    val metrics = paint.fontMetrics
    canvas.drawText(text, centerX, centerY - (metrics.ascent + metrics.descent) / 2, paint)
  }
  override fun setAlpha(alpha: Int) { paint.alpha = alpha; invalidateSelf() }
  override fun setColorFilter(filter: ColorFilter?) { paint.colorFilter = filter; invalidateSelf() }
  @Deprecated("Deprecated in Java")
  override fun getOpacity() = PixelFormat.TRANSLUCENT
}
