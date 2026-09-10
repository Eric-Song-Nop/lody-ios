package app.innei.lody.kit.runtime

import org.json.JSONArray

internal interface RuntimeEndpoint {
  fun invoke(method: String, args: JSONArray = JSONArray(), completion: (Result<Any?>) -> Unit = {})
  fun suspend()
  fun resume()
  fun close()
}
