package app.innei.lody.kit.list

import android.content.Context
import android.content.res.ColorStateList
import android.content.res.Configuration
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.RippleDrawable
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.view.ViewCompat
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import app.innei.lody.kit.chrome.LodySymbols
import app.innei.lody.kit.chrome.LodyUiColors
import expo.modules.kotlin.AppContext
import expo.modules.kotlin.records.Field
import expo.modules.kotlin.records.Record
import expo.modules.kotlin.viewevent.EventDispatcher
import expo.modules.kotlin.views.ExpoView

class LodyListRow : Record {
  @Field var id: String = ""
  @Field var title: String = ""
  @Field var subtitle: String = ""
  @Field var subtitleMono: Boolean = false
  @Field var value: String = ""
  @Field var image: String = ""
  @Field var action: Boolean = false
  @Field var navigates: Boolean = false
  @Field var disclosure: Boolean = false
  @Field var destructive: Boolean = false
}
class LodyListSection : Record {
  @Field var id: String = ""
  @Field var header: String = ""
  @Field var footer: String = ""
  @Field var rows: List<LodyListRow> = emptyList()
}
private data class Item(
  val section: String, val id: String, val kind: Int, val title: String,
  val subtitle: String = "", val value: String = "", val image: String = "",
  val mono: Boolean = false, val actionable: Boolean = false,
  val disclosure: Boolean = false, val destructive: Boolean = false,
  val navigates: Boolean = false,
)

class LodyGroupedList(context: Context, appContext: AppContext) : ExpoView(context, appContext) {
  override val shouldUseAndroidLayout = true
  private val onRowPress by EventDispatcher()
  private val onRefresh by EventDispatcher()
  private val refresh = SwipeRefreshLayout(context)
  private val list = RecyclerView(context)
  private val rows = Rows()
  private var placeholder = ""
  private var sections: List<LodyListSection> = emptyList()
  private var transparent = false
  private var accent: String? = null
  private var refreshEnabled = false
  private var navigationFocusId: String? = null
  private var restoreNavigationFocus = false

  init {
    orientation = VERTICAL
    list.layoutManager = LinearLayoutManager(context)
    list.adapter = rows
    list.clipToPadding = false
    list.itemAnimator = null
    refresh.addView(list, ViewGroup.LayoutParams(-1, -1))
    refresh.isEnabled = false
    // RecyclerView still nests into refresh; unconsumed pull must not drag a sheet.
    refresh.isNestedScrollingEnabled = false
    refresh.setOnRefreshListener {
      if (refreshEnabled) onRefresh(emptyMap<String, Any>())
    }
    addView(refresh, LayoutParams(-1, -1))
    updateColors()
  }

  override fun dispatchTouchEvent(event: MotionEvent): Boolean {
    if (event.actionMasked == MotionEvent.ACTION_DOWN) {
      navigationFocusId = null
      restoreNavigationFocus = false
      disallowAncestorIntercept(true)
    }
    return try { super.dispatchTouchEvent(event) } finally {
      if (event.actionMasked == MotionEvent.ACTION_UP || event.actionMasked == MotionEvent.ACTION_CANCEL) {
        disallowAncestorIntercept(false)
      }
    }
  }

  override fun onDetachedFromWindow() {
    if (navigationFocusId != null) restoreNavigationFocus = true
    super.onDetachedFromWindow()
  }
  override fun onAttachedToWindow() {
    super.onAttachedToWindow()
    post { restoreReturningRowFocus() }
  }
  override fun onVisibilityChanged(changedView: View, visibility: Int) {
    super.onVisibilityChanged(changedView, visibility)
    if (!isShown && navigationFocusId != null) restoreNavigationFocus = true
    if (isShown) post { restoreReturningRowFocus() }
  }
  override fun onLayout(changed: Boolean, left: Int, top: Int, right: Int, bottom: Int) {
    super.onLayout(changed, left, top, right, bottom)
    restoreReturningRowFocus()
  }
  private fun restoreReturningRowFocus() {
    val id = navigationFocusId ?: return
    if (!restoreNavigationFocus || !isAttachedToWindow || !isShown) return
    // A keyboard-activated navigation row owns its return focus, never a touch row.
    // Do not take focus from another control or resurrect a removed row.
    if (isInTouchMode || rootView.findFocus() != null) {
      navigationFocusId = null
      restoreNavigationFocus = false
      return
    }
    val position = rows.currentList.indexOfFirst { it.id == id && it.navigates }
    if (position < 0) {
      navigationFocusId = null
      restoreNavigationFocus = false
      return
    }
    val holder = list.findViewHolderForAdapterPosition(position) ?: return
    if (holder.itemView.requestFocus()) {
      navigationFocusId = null
      restoreNavigationFocus = false
    }
  }
  private fun disallowAncestorIntercept(disallow: Boolean) {
    // RN sheet roots intentionally swallow propagation, so address each ancestor.
    // Only gestures beginning inside this list are claimed; sheet chrome stays native.
    var ancestor = parent
    while (ancestor != null) {
      ancestor.requestDisallowInterceptTouchEvent(disallow)
      ancestor = ancestor.parent
    }
  }

  fun setSections(value: List<LodyListSection>) {
    require(value.all { it.id.isNotBlank() } && value.map { it.id }.distinct().size == value.size) { "List section IDs must be nonempty and unique" }
    val allRows = value.flatMap { it.rows }
    require(allRows.all { it.id.isNotBlank() } && allRows.map { it.id }.distinct().size == allRows.size) { "List row IDs must be nonempty and globally unique" }
    allRows.filter { it.image.isNotEmpty() }.forEach { LodySymbols.resource(it.image) }
    sections = value
    submit()
  }
  fun setPlaceholder(value: String) { placeholder = value; submit() }
  fun setTransparent(value: Boolean) { transparent = value; updateColors() }
  fun setAccent(value: String?) { value?.let(Color::parseColor); accent = value; updateColors() }
  fun setBottomInset(value: Float) {
    require(value.isFinite() && value >= 0) { "List inset must be nonnegative" }
    list.setPadding(0, 0, 0, dp(value))
  }
  fun setRefreshEnabled(value: Boolean) {
    refreshEnabled = value
    refresh.isEnabled = value
    if (!value) refresh.isRefreshing = false
  }
  fun setRefreshing(value: Boolean) { refresh.isRefreshing = value }

  private fun submit() {
    val items = sections.flatMap { section ->
      buildList {
        if (section.header.isNotEmpty()) add(Item(section.id, "", 1, section.header))
        section.rows.forEach { row ->
          add(Item(section.id, row.id, 0, row.title, row.subtitle, row.value, row.image,
            row.subtitleMono, row.action || row.navigates, row.disclosure, row.destructive, row.navigates))
        }
        if (section.footer.isNotEmpty()) add(Item(section.id, "", 2, section.footer))
      }
    }.toMutableList()
    if (sections.all { it.rows.isEmpty() } && placeholder.isNotEmpty()) items.add(Item("", "", 3, placeholder))
    rows.submitList(items)
  }
  private fun dp(value: Float) = LodyUiColors.dp(context, value)
  private fun actionColor() = accent?.let(Color::parseColor) ?: LodyUiColors.action(context)
  private fun updateColors() {
    setBackgroundColor(if (transparent) Color.TRANSPARENT else LodyUiColors.surface(context))
    refresh.setColorSchemeColors(actionColor())
    refresh.setProgressBackgroundColorSchemeColor(LodyUiColors.surface(context))
    rows.notifyItemRangeChanged(0, rows.itemCount)
  }
  override fun onConfigurationChanged(configuration: Configuration) {
    super.onConfigurationChanged(configuration)
    updateColors()
  }

  private inner class Holder(val box: LinearLayout) : RecyclerView.ViewHolder(box) {
    val leading = ImageView(context)
    val title = TextView(context)
    val subtitle = TextView(context)
    val value = TextView(context)
    val copy = LinearLayout(context)
    init {
      box.orientation = LinearLayout.HORIZONTAL
      box.gravity = Gravity.CENTER_VERTICAL
      box.setPadding(dp(16f), dp(12f), dp(16f), dp(12f))
      box.minimumHeight = dp(48f)
      leading.importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
      box.addView(leading, LinearLayout.LayoutParams(dp(24f), dp(24f)).apply { marginEnd = dp(16f) })
      copy.orientation = LinearLayout.VERTICAL
      copy.addView(title, LinearLayout.LayoutParams(-1, -2))
      copy.addView(subtitle, LinearLayout.LayoutParams(-1, -2))
      box.addView(copy, LinearLayout.LayoutParams(0, -2, 1f))
      box.addView(value, LinearLayout.LayoutParams(-2, -2).apply { marginStart = dp(16f) })
      listOf(title, subtitle, value).forEach { it.importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO }
      box.setOnClickListener {
        val position = bindingAdapterPosition
        if (position != RecyclerView.NO_POSITION) {
          val item = rows.currentList[position]
          if (item.actionable && isShown) {
            navigationFocusId = if (item.navigates && box.hasFocus() && !box.isInTouchMode) item.id else null
            restoreNavigationFocus = false
            onRowPress(mapOf("id" to item.id))
          }
        }
      }
    }
    fun bind(item: Item) {
      val dark = LodyUiColors.dark(context)
      val primary = if (dark) Color.WHITE else Color.parseColor("#1B1B1B")
      val secondary = Color.parseColor(if (dark) "#C6C6C6" else "#5E5E5E")
      val danger = Color.parseColor(if (dark) "#FFB4AB" else "#BA1A1A")
      val row = item.kind == 0
      title.text = item.title
      title.textSize = if (row) 16f else 14f
      title.setTextColor(when { item.destructive -> danger; item.kind == 1 -> actionColor(); else -> primary })
      title.setTypeface(null, if (item.kind == 1) Typeface.BOLD else Typeface.NORMAL)
      subtitle.text = item.subtitle
      subtitle.textSize = 14f
      subtitle.setTextColor(secondary)
      subtitle.typeface = if (item.mono) Typeface.MONOSPACE else Typeface.DEFAULT
      subtitle.visibility = if (item.subtitle.isEmpty()) GONE else VISIBLE
      value.text = listOf(item.value, if (item.disclosure) "›" else "").filter { it.isNotEmpty() }.joinToString("  ")
      value.textSize = 14f
      value.maxWidth = dp(120f)
      value.setTextColor(secondary)
      value.visibility = if (value.text.isEmpty()) GONE else VISIBLE
      val icon = if (item.image.isEmpty()) null else context.getDrawable(LodySymbols.resource(item.image))?.mutate()?.apply {
        setTint(if (item.destructive) danger else actionColor())
        setBounds(0, 0, dp(24f), dp(24f))
      }
      leading.setImageDrawable(icon)
      leading.visibility = if (icon == null) GONE else VISIBLE
      box.background = if (item.actionable) RippleDrawable(ColorStateList.valueOf(actionColor() and 0x00FFFFFF or 0x22000000), ColorDrawable(Color.TRANSPARENT), ColorDrawable(Color.WHITE)) else null
      box.isClickable = item.actionable
      box.isFocusable = item.actionable
      box.isSelected = false
      box.contentDescription = listOf(item.title, item.subtitle, item.value).filter { it.isNotEmpty() }.joinToString(", ")
      ViewCompat.setAccessibilityHeading(box, item.kind == 1)
      ViewCompat.setScreenReaderFocusable(box, true)
    }
  }
  private inner class Rows : ListAdapter<Item, Holder>(object : DiffUtil.ItemCallback<Item>() {
    override fun areItemsTheSame(old: Item, new: Item) = old.section == new.section && old.id == new.id && old.kind == new.kind
    override fun areContentsTheSame(old: Item, new: Item) = old == new
  }) {
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int) = Holder(LinearLayout(parent.context).apply {
      layoutParams = RecyclerView.LayoutParams(-1, -2)
    })
    override fun onBindViewHolder(holder: Holder, position: Int) = holder.bind(getItem(position))
  }
}
