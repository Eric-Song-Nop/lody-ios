package app.innei.lody.kit.locale

import android.content.Context

internal object LodyStrings {
  private val placeholder = Regex("\\{([A-Za-z][A-Za-z0-9_]*)\\}")

  fun text(context: Context, key: String, arguments: Map<String, String> = emptyMap(), count: Int? = null): String {
    val entry = requireNotNull(lodyStringEntries[key]) { "Unknown native string: $key" }
    require(entry.plural == (count != null)) { "Plural quantity required only for plural strings: $key" }
    val values = arguments.toMutableMap()
    if (count != null && "count" in entry.parameters) {
      require("count" !in values) { "Quantity owns the count argument" }
      values["count"] = count.toString()
    }
    require(values.keys == entry.parameters) { "Wrong native string arguments: $key" }
    val template = if (count == null) context.getString(entry.id) else context.resources.getQuantityText(entry.id, count).toString()
    // Regex.replace visits the template once; argument contents remain literal.
    return placeholder.replace(template) { match -> values.getValue(match.groupValues[1]) }
  }
}
