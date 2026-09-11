package app.innei.lody.kit.locale

import android.content.Context
import android.content.res.Configuration
import org.json.JSONArray
import org.json.JSONObject
import java.util.Locale

internal object LocaleVerification {
  fun run(context: Context): String {
    val results = JSONArray()
    for (language in listOf("en", "zh-Hans", "es")) {
      val configuration = Configuration(context.resources.configuration)
      configuration.setLocale(Locale.forLanguageTag(language))
      val localized = context.createConfigurationContext(configuration)
      for ((key, entry) in lodyStringEntries) {
        val counts: List<Int?> = if (entry.plural) listOf(0, 1, 2) else listOf(null)
        for (count in counts) {
          val arguments = entry.parameters.filter { count == null || it != "count" }.associateWith { "[$it] 100% {$it} & <x> \"quoted\" \\path" }
          results.put(JSONObject().put("locale", language).put("key", key).put("count", count ?: JSONObject.NULL)
            .put("arguments", JSONObject(arguments)).put("text", LodyStrings.text(localized, key, arguments, count)))
        }
      }
    }
    fun rejects(action: () -> Unit): Boolean = try { action(); false } catch (_: IllegalArgumentException) { true }
    check(rejects { LodyStrings.text(context, "native.missing") })
    check(rejects { LodyStrings.text(context, "native.chat.composer.modelPicker") })
    check(rejects { LodyStrings.text(context, "native.chat.transcript.fileCount") })
    check(rejects { LodyStrings.text(context, "native.close", count = 1) })
    return JSONObject().put("entries", results).put("rejectedInvalidInputs", 4).toString()
  }
}
