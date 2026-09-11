package app.innei.lody.kit.feedback

import android.content.Context
import android.content.res.ColorStateList
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.RippleDrawable
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.view.accessibility.AccessibilityManager
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import app.innei.lody.kit.chrome.LodyUiColors
import app.innei.lody.kit.chrome.LodySymbols
import app.innei.lody.kit.locale.LodyStrings
import java.lang.ref.WeakReference

/** One module-owned native surface, moved between Activity and Dialog decor views. */
internal class LodyFeedback {
  private class Notice(val text: String, val kind: String)
  private val main = Handler(Looper.getMainLooper())
  private val hosts = mutableListOf<WeakReference<LodyFeedbackHost>>()
  private var root: ViewGroup? = null
  private var overlay: FrameLayout? = null
  private var toastColumn: LinearLayout? = null
  private var bannerRow: View? = null
  private var renderedBanner: Notice? = null
  private val toastViews = mutableMapOf<Notice, View>()
  private val toasts = mutableListOf<Notice>()
  private var banner: Notice? = null
  private var toastDeadline = 0L
  private var bannerDeadline = 0L
  private var foreground = true
  @Volatile private var closed = false
  private val expire = Runnable {
    expireNotices()
    render()
    scheduleExpiration()
  }

  fun register(host: LodyFeedbackHost) {
    hosts.removeAll { it.get() == null || it.get() === host }
    hosts.add(WeakReference(host))
    refreshHost()
  }

  fun unregister(host: LodyFeedbackHost) {
    hosts.removeAll { it.get() == null || it.get() === host }
    refreshHost()
  }

  fun activeView(): View? = hosts.asReversed().firstNotNullOfOrNull { reference ->
    reference.get()?.takeIf { it.isAttachedToWindow && it.isShown && it.hasWindowFocus() }
  }

  fun refreshHost(rebuild: Boolean = false) {
    if (closed) return
    val next = if (foreground) activeView()?.rootView as? ViewGroup else null
    if (next !== root || rebuild) {
      detachSurface()
      root = next
      expireNotices()
      render()
    } else {
      applyInsets(next?.let(ViewCompat::getRootWindowInsets))
    }
  }

  // The public void facade requests a transient UI update, just as on iOS.
  // Validate synchronously, then perform all View work on the main thread.
  fun showToast(text: String, kind: String) {
    require(kind in setOf("info", "warning", "error")) { "Invalid toast kind" }
    if (text.isBlank()) return
    check(!closed) { "Feedback owner is closed" }
    main.post {
      if (closed || !foreground) return@post
      refreshHost()
      val notice = Notice(text, kind)
      val last = toasts.lastOrNull()
      if (last?.text != text || last.kind != kind) toasts.add(notice)
      while (toasts.size > 3) toasts.removeAt(0)
      toastDeadline = SystemClock.uptimeMillis() + timeout(3200)
      render()
      scheduleExpiration()
      haptic(kind == "error")
    }
  }

  fun showBanner(text: String, kind: String) {
    require(kind in setOf("completed", "attention")) { "Invalid banner kind" }
    if (text.isBlank()) return
    check(!closed) { "Feedback owner is closed" }
    main.post {
      if (closed || !foreground) return@post
      refreshHost()
      banner = Notice(text, kind)
      bannerDeadline = if (kind == "attention") 0 else SystemClock.uptimeMillis() + timeout(4000)
      render()
      scheduleExpiration()
      haptic(false)
    }
  }

  fun dismissBanner() {
    main.post {
      banner = null
      bannerDeadline = 0
      render()
      scheduleExpiration()
    }
  }

  fun enterBackground() {
    foreground = false
    clear()
  }

  fun enterForeground() {
    foreground = true
    refreshHost()
  }

  fun close() {
    closed = true
    clear()
    hosts.clear()
  }

  private fun clear() {
    toasts.clear()
    banner = null
    toastDeadline = 0
    bannerDeadline = 0
    main.removeCallbacks(expire)
    detachSurface()
    root = null
  }

  private fun timeout(base: Int): Long {
    val manager = root?.context?.getSystemService(AccessibilityManager::class.java) ?: return base.toLong()
    if (Build.VERSION.SDK_INT >= 29) {
      return manager.getRecommendedTimeoutMillis(base, AccessibilityManager.FLAG_CONTENT_TEXT or AccessibilityManager.FLAG_CONTENT_CONTROLS).toLong()
    }
    // Older Android has no timeout recommendation API; let accessibility users dismiss.
    return if (manager.isTouchExplorationEnabled) Int.MAX_VALUE.toLong() else base.toLong()
  }

  private fun haptic(error: Boolean) {
    val effect = if (Build.VERSION.SDK_INT >= 30) {
      if (error) android.view.HapticFeedbackConstants.REJECT else android.view.HapticFeedbackConstants.CONFIRM
    } else android.view.HapticFeedbackConstants.CLOCK_TICK
    activeView()?.performHapticFeedback(effect)
  }

  private fun expireNotices() {
    val now = SystemClock.uptimeMillis()
    if (toastDeadline > 0 && now >= toastDeadline) {
      toasts.clear()
      toastDeadline = 0
    }
    if (bannerDeadline > 0 && now >= bannerDeadline) {
      banner = null
      bannerDeadline = 0
    }
  }

  private fun scheduleExpiration() {
    main.removeCallbacks(expire)
    val deadline = listOf(toastDeadline, bannerDeadline).filter { it > 0 }.minOrNull() ?: return
    main.postAtTime(expire, deadline)
  }

  private fun detachSurface() {
    overlay?.let { (it.parent as? ViewGroup)?.removeView(it) }
    overlay = null
    toastColumn = null
    bannerRow = null
    renderedBanner = null
    toastViews.clear()
  }

  private fun render() {
    if (closed || !foreground || (toasts.isEmpty() && banner == null)) {
      detachSurface()
      return
    }
    val parent = root ?: return
    if (!parent.isAttachedToWindow) return
    // These children belong to Android, never Yoga. Empty surface areas pass touches through.
    val surface = overlay ?: FrameLayout(parent.context).also {
      it.isClickable = false
      it.isFocusable = false
      it.importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
      it.elevation = dp(parent.context, 16).toFloat()
      parent.addView(it, ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))
      overlay = it
      ViewCompat.setOnApplyWindowInsetsListener(it) { _, insets -> applyInsets(insets); insets }
      ViewCompat.requestApplyInsets(it)
    }
    val context = surface.context
    val column = toastColumn ?: LinearLayout(context).apply {
      orientation = LinearLayout.VERTICAL
      clipChildren = false
      clipToPadding = false
      toastColumn = this
      surface.addView(this, FrameLayout.LayoutParams(-1, -2, Gravity.BOTTOM or Gravity.CENTER_HORIZONTAL))
    }
    toastViews.keys.filter { it !in toasts }.forEach { notice -> column.removeView(toastViews.remove(notice)) }
    toasts.forEach { notice ->
      if (notice !in toastViews) {
        val view = card(context, notice, false) {
          toasts.remove(notice)
          if (toasts.isEmpty()) toastDeadline = 0
          render()
          scheduleExpiration()
        }
        toastViews[notice] = view
        column.addView(view, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(context, 8) })
      }
    }
    if (renderedBanner !== banner) {
      bannerRow?.let(surface::removeView)
      bannerRow = banner?.let { notice ->
        card(context, notice, true) { dismissBanner() }.also {
          surface.addView(it, FrameLayout.LayoutParams(-1, -2, Gravity.TOP or Gravity.CENTER_HORIZONTAL))
        }
      }
      renderedBanner = banner
    }
    applyInsets(ViewCompat.getRootWindowInsets(parent))
  }

  private fun applyInsets(insets: WindowInsetsCompat?) {
    val surface = overlay ?: return
    val bars = insets?.getInsets(WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout())
    val bottom = insets?.getInsets(WindowInsetsCompat.Type.ime())?.bottom ?: 0
    val margin = dp(surface.context, 16)
    toastColumn?.let { column ->
      column.layoutParams = (column.layoutParams as FrameLayout.LayoutParams).apply {
        leftMargin = margin + (bars?.left ?: 0)
        rightMargin = margin + (bars?.right ?: 0)
        bottomMargin = margin + maxOf(bars?.bottom ?: 0, bottom)
      }
    }
    bannerRow?.let { row ->
      // The marker is at the page content origin, below its native stack header.
      // Convert within this window; Activity and Dialog coordinates are not interchangeable.
      val contentOrigin = IntArray(2)
      val rootOrigin = IntArray(2)
      activeView()?.getLocationInWindow(contentOrigin)
      root?.getLocationInWindow(rootOrigin)
      row.layoutParams = (row.layoutParams as FrameLayout.LayoutParams).apply {
        leftMargin = margin + (bars?.left ?: 0)
        rightMargin = margin + (bars?.right ?: 0)
        topMargin = dp(surface.context, 8) + maxOf(bars?.top ?: 0, contentOrigin[1] - rootOrigin[1])
      }
    }
  }

  private fun card(context: Context, notice: Notice, isBanner: Boolean, dismiss: () -> Unit): View {
    val row = LinearLayout(context).apply {
      orientation = LinearLayout.HORIZONTAL
      gravity = Gravity.CENTER_VERTICAL
      minimumHeight = dp(context, 48)
      setPadding(dp(context, 16), dp(context, 8), 0, dp(context, 8))
      elevation = dp(context, 4).toFloat()
      setOnClickListener { dismiss() }
    }
    val background = GradientDrawable().apply {
      cornerRadius = dp(context, 12).toFloat()
      setColor(LodyUiColors.surface(context))
      setStroke(dp(context, 1), LodyUiColors.action(context))
    }
    row.background = RippleDrawable(ColorStateList.valueOf(LodyUiColors.actionSurface(context)), background, null)
    val label = if (isBanner) notice.text + "\n" + LodyStrings.text(context, "native.session.banner.${notice.kind}") else notice.text
    val text = TextView(context).apply {
      this.text = label
      textSize = 16f
      maxLines = if (isBanner) 3 else 4
      ellipsize = android.text.TextUtils.TruncateAt.END
      contentDescription = label
      setTextColor(when (notice.kind) {
        "error" -> Color.parseColor(if (LodyUiColors.dark(context)) "#FFB4AB" else "#BA1A1A")
        "warning", "attention" -> Color.parseColor(if (LodyUiColors.dark(context)) "#FFCC80" else "#855400")
        else -> LodyUiColors.text(context)
      })
      if (isBanner) setTypeface(typeface, Typeface.BOLD)
      accessibilityLiveRegion = View.ACCESSIBILITY_LIVE_REGION_POLITE
    }
    row.addView(text, LinearLayout.LayoutParams(0, -2, 1f))
    val close = android.widget.ImageButton(context).apply {
      setImageResource(LodySymbols.resource("xmark"))
      setPadding(dp(context, 12), dp(context, 12), dp(context, 12), dp(context, 12))
      imageTintList = ColorStateList.valueOf(LodyUiColors.action(context))
      this.background = RippleDrawable(ColorStateList.valueOf(LodyUiColors.actionSurface(context)), null, null)
      contentDescription = LodyStrings.text(context, "native.close") + ": " + label.replace('\n', ' ')
      minimumWidth = dp(context, 48)
      minimumHeight = dp(context, 48)
      setOnClickListener { dismiss() }
    }
    row.addView(close, LinearLayout.LayoutParams(dp(context, 48), dp(context, 48)))
    return row
  }

  private fun dp(context: Context, value: Int) = LodyUiColors.dp(context, value.toFloat())
}
