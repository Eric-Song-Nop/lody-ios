package app.innei.lody.kit.preferences

import android.content.Context

/** Display preferences only. Credentials and account projections have separate owners. */
internal class InboxPreferences(context: Context) {
  private val preferences = context.getSharedPreferences("lody_inbox", Context.MODE_PRIVATE)
  private val prefix = "expanded:"

  @Synchronized fun initialView(): Int = if (preferences.getInt("view", 0) == 1) 1 else 0
  @Synchronized fun saveView(index: Int) {
    check(preferences.edit().putInt("view", if (index == 1) 1 else 0).commit()) { "inbox_preferences_write_failed" }
  }
  @Synchronized fun readExpansion(): Map<String, Boolean> = preferences.all.filterKeys { it.startsWith(prefix) }.mapKeys { it.key.removePrefix(prefix) }.mapValues {
    it.value as? Boolean ?: error("inbox_preferences_invalid")
  }
  @Synchronized fun saveExpansion(projectId: String, expanded: Boolean) {
    require(projectId.isNotEmpty() && projectId.length <= 1024) { "inbox_project_id_invalid" }
    check(preferences.edit().putBoolean(prefix + projectId, expanded).commit()) { "inbox_preferences_write_failed" }
  }
}
