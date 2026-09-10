package app.innei.lody.kit.chrome

import android.content.Context
import android.content.res.Configuration
import android.graphics.Color

internal object LodyUiColors {
  fun dark(context: Context) = context.resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK == Configuration.UI_MODE_NIGHT_YES
  fun text(context: Context): Int {
    val values = context.obtainStyledAttributes(intArrayOf(android.R.attr.textColorPrimary))
    return try { values.getColor(0, if (dark(context)) Color.WHITE else Color.BLACK) } finally { values.recycle() }
  }
  fun action(context: Context) = Color.parseColor(if (dark(context)) "#90CAF9" else "#1565C0")
  fun surface(context: Context) = Color.parseColor(if (dark(context)) "#252525" else "#F3F3F3")
  fun actionSurface(context: Context) = Color.parseColor(if (dark(context)) "#1E3A5F" else "#E8F0FE")
  fun tint(context: Context, value: String?) = value?.takeIf { it.isNotBlank() }?.let(Color::parseColor) ?: text(context)
  fun dp(context: Context, value: Float) = (value * context.resources.displayMetrics.density).toInt()
}
