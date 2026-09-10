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
  )

  fun resource(symbol: String): Int = requireNotNull(resources[symbol]) {
    "Android symbol has no semantic mapping: $symbol"
  }
}
