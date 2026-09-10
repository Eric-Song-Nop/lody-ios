package app.innei.lody.kit.storage

import android.content.Context
import android.database.sqlite.SQLiteDatabase
import java.io.File
import org.json.JSONArray
import org.json.JSONObject

/** Complete display projections, never credentials or a second CRDT replica. */
internal class LocalStore(context: Context, name: String = "catalog") : AutoCloseable {
  private val path = File(context.noBackupFilesDir, "$name.sqlite")
  private var db: SQLiteDatabase? = null
  private val epoch = java.util.concurrent.atomic.AtomicLong()
  val generation: Long get() = epoch.get()

  private fun database(): SQLiteDatabase {
    db?.let { return it }
    path.parentFile?.mkdirs()
    // The default handler deletes corrupt files and may reopen an empty database.
    // Surface the failure until an explicit clear owns the destructive recovery.
    val opened = SQLiteDatabase.openOrCreateDatabase(path.path, null) {
      throw android.database.sqlite.SQLiteDatabaseCorruptException("storage_database_corrupt")
    }
    try {
      check(opened.version <= 1) { "storage_schema_unsupported" }
      opened.execSQL("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
      opened.version = 1
      db = opened
      return opened
    } catch (error: Exception) { opened.close(); throw error }
  }

  @Synchronized fun read(key: String): String? {
    require(key.toByteArray().size <= 1024) { "storage_key_limit" }
    val database = database()
    val length = database.rawQuery("SELECT length(value) FROM cache WHERE key = ?", arrayOf(key)).use {
      if (!it.moveToFirst()) return null
      it.getInt(0)
    }
    check(length <= 12 * 1024 * 1024) { "storage_value_limit" }
    // Avoid CursorWindow's per-row limit when restoring a complete large projection.
    val value = StringBuilder()
    var offset = 1
    while (offset <= length) {
      database.rawQuery("SELECT substr(value, ?, 65536) FROM cache WHERE key = ?", arrayOf(offset.toString(), key)).use {
        check(it.moveToFirst()) { "storage_read_changed" }
        value.append(it.getString(0))
      }
      offset += 65536
    }
    return value.toString().also { check(it.toByteArray().size <= 12 * 1024 * 1024) { "storage_value_limit" } }
  }

  @Synchronized fun write(key: String, value: String, expectedGeneration: Long = generation) {
    check(expectedGeneration == generation) { "storage_context_replaced" }
    require(!key.contains('\u0000') && !value.contains('\u0000') && key.toByteArray().size <= 1024 && value.toByteArray().size <= 12 * 1024 * 1024) { "storage_value_limit" }
    database().execSQL("INSERT OR REPLACE INTO cache(key, value) VALUES (?, ?)", arrayOf(key, value))
  }

  fun invalidate(): Long = epoch.incrementAndGet()
  @Synchronized fun clear() {
    invalidate()
    try { database().execSQL("DELETE FROM cache") }
    catch (_: android.database.sqlite.SQLiteDatabaseCorruptException) {
      close()
      check(SQLiteDatabase.deleteDatabase(path)) { "storage_reset_failed" }
      database()
    }
  }

  @Synchronized fun startup(): Map<String, String> {
    val account = read("account") ?: return emptyMap()
    val parsed = JSONObject(account)
    val id = parsed.getJSONObject("user").getString("id")
    val workspaces = parsed.getJSONArray("workspaces")
    val selected = read("workspace:$id")?.let { JSONArray("[$it]").optString(0) }
    var workspace = ""
    for (index in 0 until workspaces.length()) {
      val candidate = workspaces.getJSONObject(index).getString("id")
      if (index == 0) workspace = candidate
      if (candidate == selected) { workspace = candidate; break }
    }
    return mapOf("account" to account, "workspace" to workspace, "catalog" to (read("catalog:$id:$workspace") ?: "null"))
  }

  @Synchronized override fun close() { db?.close(); db = null }
}
