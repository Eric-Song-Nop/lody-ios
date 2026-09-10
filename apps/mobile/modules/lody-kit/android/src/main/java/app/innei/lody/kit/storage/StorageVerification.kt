package app.innei.lody.kit.storage

import android.content.Context
import android.os.Process
import android.os.SystemClock
import org.json.JSONArray
import org.json.JSONObject

/** Two invocations separated by a real force-stop; only non-secret fixture data is reported. */
internal class StorageVerification(private val context: Context) {
  fun run(seedCatalog: String?): String {
    val store = LocalStore(context, "verification-catalog")
    val auth = AuthCredentials(context, "verification-session")
    try {
      val prepared = store.read("verification:prepared")
      if (prepared == null) {
        if (seedCatalog == null) return JSONObject().put("status", "needs_runtime").toString()
        val runtimeCatalog = JSONObject().put("catalog", JSONObject(seedCatalog)).put("syncedAt", 1).toString()
        store.clear()
        auth.clear()
        val token = "offline-storage-fixture-" + java.util.UUID.randomUUID()
        auth.save(token)
        check(auth.read() == token)
        check(!auth.ciphertextForVerification().toString(Charsets.ISO_8859_1).contains(token))
        store.write("account", account("a"))
        store.write("workspace:a", "\"a-two\"")
        store.write("catalog:a:a-one", "{\"fixture\":\"wrong-workspace\"}")
        store.write("catalog:a:a-two", runtimeCatalog)
        store.write("verification:large", largeCatalog())
        store.write("verification:prepared", JSONObject().put("pid", Process.myPid()).put("tokenHash", hash(token)).put("catalogHash", hash(runtimeCatalog)).toString())
        return JSONObject().put("status", "prepared").put("fixtureVersion", "storage-v1").put("processId", Process.myPid()).toString()
      }
      val prior = JSONObject(prepared)
      check(prior.getInt("pid") != Process.myPid()) { "process_restart_required" }
      val checks = JSONArray()
      val started = SystemClock.elapsedRealtime()
      val startup = store.startup()
      check(startup["workspace"] == "a-two" && hash(startup["catalog"] ?: "") == prior.getString("catalogHash") && store.read("verification:large") == largeCatalog()) { "offline_projection_mismatch" }
      check(hash(auth.read() ?: error("credential_missing")) == prior.getString("tokenHash")) { "credential_restore_mismatch" }
      val restoreMs = SystemClock.elapsedRealtime() - started
      pass(checks, "A-STORE-01", "Real process restart restored encrypted credentials, an actual WASM catalog, and a separate large Unicode projection")

      store.write("account", account("b"))
      check(store.startup()["workspace"] == "b-one" && store.startup()["catalog"] == "null")
      store.write("catalog:b:b-one", "{\"fixture\":\"account-b\"}")
      check(store.startup()["catalog"] == "{\"fixture\":\"account-b\"}")
      pass(checks, "A-STORE-02", "Account and workspace selection never restore another context's projection")

      auth.removeKeyForVerification()
      val failure = runCatching { auth.read() }.exceptionOrNull()
      check(failure?.message == "credential_reauthorization_required")
      check(auth.read() == null)
      auth.save("offline-reauthorized")
      check(auth.read() == "offline-reauthorized")
      pass(checks, "A-STORE-03", "Actual Keystore key loss requires authorization and a newly generated key can save/read again")

      val previous = store.generation
      store.invalidate()
      store.clear()
      auth.clear()
      check(runCatching { store.write("account", account("a"), previous) }.isFailure)
      check(store.startup().isEmpty() && auth.read() == null)
      store.write("account", "broken-json")
      check(runCatching { store.startup() }.isFailure)
      store.clear()
      check(store.startup().isEmpty())
      pass(checks, "A-STORE-04", "Clear fences delayed old writes; malformed saved context fails explicitly and can be cleared")
      return JSONObject().put("status", "pass").put("fixtureVersion", "storage-v1")
        .put("cases", checks).put("priorProcessId", prior.getInt("pid")).put("processId", Process.myPid())
        .put("projectionUtf8Bytes", largeCatalog().toByteArray().size).put("restoreMs", restoreMs)
        .put("runtimeCatalogSha256", prior.getString("catalogHash")).put("runtimeSeeded", true)
        .put("credentialPlaintextPersisted", false).toString()
    } finally { store.close() }
  }

  private fun account(id: String) = JSONObject().put("user", JSONObject().put("id", id))
    .put("workspaces", JSONArray().put(JSONObject().put("id", "$id-one")).put(JSONObject().put("id", "$id-two"))).toString()
  private fun largeCatalog() = JSONObject().put("catalog", JSONObject().put("fixture", "离线🙂".repeat(300_000))).put("syncedAt", 1).toString()
  private fun hash(value: String) = java.security.MessageDigest.getInstance("SHA-256").digest(value.toByteArray()).joinToString("") { "%02x".format(it) }
  private fun pass(checks: JSONArray, id: String, detail: String) { checks.put(JSONObject().put("id", id).put("status", "pass").put("detail", detail)) }
}
