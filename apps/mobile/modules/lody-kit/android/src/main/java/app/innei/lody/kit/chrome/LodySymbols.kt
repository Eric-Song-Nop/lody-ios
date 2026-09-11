package app.innei.lody.kit.chrome

import app.innei.lody.kit.R

internal object LodySymbols {
  private val resources = mapOf(
    "folder" to R.drawable.lody_folder_outline,
    "folder.fill" to R.drawable.lody_folder,
    "gearshape" to R.drawable.lody_settings_outline,
    "gearshape.fill" to R.drawable.lody_settings,
    "plus" to R.drawable.lody_add,
    "magnifyingglass" to R.drawable.lody_search,
    "checkmark" to R.drawable.lody_check,
    "xmark" to R.drawable.lody_close,
    "ellipsis" to R.drawable.lody_more_horiz,
    "person" to R.drawable.lody_person_outline,
    "info.circle" to R.drawable.lody_info_outline,
    "circle" to R.drawable.lody_circle_outline,
    "archivebox" to R.drawable.lody_archive_outline,
    "arrow.clockwise" to R.drawable.lody_refresh,
    "bell" to R.drawable.lody_notifications_outline,
    "bubble.left.and.text.bubble.right.fill" to R.drawable.lody_forum,
    "circle.fill" to R.drawable.lody_circle,
    "cpu" to R.drawable.lody_memory,
    "desktopcomputer" to R.drawable.lody_desktop_windows_outline,
    "doc.on.doc" to R.drawable.lody_content_copy_outline,
    "doc.text" to R.drawable.lody_description_outline,
    "doc.text.magnifyingglass" to R.drawable.lody_find_in_page_outline,
    "globe" to R.drawable.lody_language,
    "ladybug" to R.drawable.lody_bug_report_outline,
    "lock.shield.fill" to R.drawable.lody_shield_lock,
    "paperplane.fill" to R.drawable.lody_send,
    "person.2.fill" to R.drawable.lody_group,
    "sparkles" to R.drawable.lody_auto_awesome,
    "square.and.pencil" to R.drawable.lody_edit_square_outline,
    "terminal" to R.drawable.lody_terminal,
    "wrench.and.screwdriver" to R.drawable.lody_construction,
    "xmark.octagon.fill" to R.drawable.lody_dangerous,
    "person.crop.circle" to R.drawable.lody_account_circle_outline,
    "puzzlepiece.extension" to R.drawable.lody_extension_outline,
    "pin" to R.drawable.lody_keep_outline,
    "pin.fill" to R.drawable.lody_keep,
    "pin.slash" to R.drawable.lody_keep_off_outline,
    "pin.slash.fill" to R.drawable.lody_keep_off,
    "tray.and.arrow.up" to R.drawable.lody_unarchive_outline,
  )

  fun resource(symbol: String): Int = requireNotNull(resources[symbol]) {
    "Android symbol has no semantic mapping: $symbol"
  }
}
