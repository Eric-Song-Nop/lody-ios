package app.innei.lody.kit.menu

import android.content.Context
import android.content.res.ColorStateList
import android.graphics.Color
import android.text.SpannableString
import android.text.Spanned
import android.text.style.ForegroundColorSpan
import android.view.Menu
import android.view.View
import androidx.appcompat.widget.PopupMenu
import app.innei.lody.kit.chrome.LodySymbols
import app.innei.lody.kit.chrome.LodyUiColors
import expo.modules.kotlin.records.Field
import expo.modules.kotlin.records.Record

class LodyMenuEntry : Record {
  @Field var id: String = ""
  @Field var title: String = ""
  @Field var symbol: String? = null
  @Field var selected: Boolean? = null
  @Field var destructive: Boolean = false
}

/** One owner per anchor. Replacing data or removing the host cancels its menu. */
class LodyPopupMenu(private val anchor: View, private val select: (String) -> Unit) {
  private var popup: PopupMenu? = null
  private var entries: List<LodyMenuEntry> = emptyList()

  fun setEntries(value: List<LodyMenuEntry>) {
    require(value.all { it.id.isNotBlank() && it.title.isNotBlank() }) { "Menu IDs and titles must not be empty" }
    require(value.map { it.id }.toSet().size == value.size) { "Menu IDs must be unique" }
    value.forEach { it.symbol?.takeIf(String::isNotBlank)?.let(LodySymbols::resource) }
    dismiss()
    entries = value.toList()
  }

  fun show(): Boolean {
    if (entries.isEmpty() || !anchor.isAttachedToWindow || !anchor.isShown || !anchor.isEnabled) return false
    if (popup != null) return true
    val snapshot = entries
    val current = PopupMenu(anchor.context, anchor)
    snapshot.forEachIndexed { index, entry ->
      val title = if (entry.destructive) SpannableString(entry.title).apply {
        setSpan(ForegroundColorSpan(dangerColor(anchor.context)), 0, length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
      } else entry.title
      current.menu.add(Menu.NONE, index + 1, index, title).apply {
        isCheckable = entry.selected != null
        isChecked = entry.selected == true
        entry.symbol?.takeIf(String::isNotBlank)?.let {
          icon = anchor.context.getDrawable(LodySymbols.resource(it))?.mutate()?.apply {
            setTintList(ColorStateList.valueOf(if (entry.destructive) dangerColor(anchor.context) else LodyUiColors.text(anchor.context)))
          }
        }
      }
    }
    current.setForceShowIcon(snapshot.any { !it.symbol.isNullOrBlank() })
    current.setOnMenuItemClickListener { item ->
      if (popup !== current || !anchor.isAttachedToWindow || !anchor.isShown) return@setOnMenuItemClickListener false
      val entry = snapshot.getOrNull(item.itemId - 1) ?: return@setOnMenuItemClickListener false
      // Invalidate before dispatch: re-entrant prop updates cannot deliver twice.
      dismiss()
      select(entry.id)
      true
    }
    current.setOnDismissListener { if (popup === current) popup = null }
    popup = current
    current.show()
    return true
  }

  fun dismiss() {
    val old = popup
    popup = null
    old?.dismiss()
  }

  private fun dangerColor(context: Context): Int =
    if (LodyUiColors.dark(context)) Color.rgb(255, 180, 171) else Color.rgb(186, 26, 26)
}
