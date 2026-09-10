package app.innei.lody.kit.storage

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.AtomicFile
import java.io.File
import java.nio.ByteBuffer
import java.security.GeneralSecurityException
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/** Call on the storage worker. Keys stay in AndroidKeyStore; only ciphertext is persisted. */
internal class AuthCredentials(context: Context, private val name: String = "better-auth-session") {
  private val file = AtomicFile(File(context.noBackupFilesDir, "$name.enc"))
  private val alias = "app.innei.lody.auth.$name.v1"
  private val aad = alias.toByteArray(Charsets.UTF_8)
  private fun keystore() = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
  private fun key(create: Boolean): SecretKey? {
    (keystore().getKey(alias, null) as? SecretKey)?.let { return it }
    if (!create) return null
    return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").apply {
      init(KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
        .setKeySize(256).setBlockModes(KeyProperties.BLOCK_MODE_GCM)
        .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
        .setRandomizedEncryptionRequired(true).build())
    }.generateKey()
  }

  @Synchronized fun save(token: String) {
    val plain = token.toByteArray(Charsets.UTF_8)
    require(plain.isNotEmpty() && plain.size <= 64 * 1024) { "credential_size_invalid" }
    try {
      val cipher = Cipher.getInstance("AES/GCM/NoPadding")
      cipher.init(Cipher.ENCRYPT_MODE, key(true))
      cipher.updateAAD(aad)
      val encrypted = cipher.doFinal(plain)
      check(cipher.iv.size == 12)
      val encoded = ByteBuffer.allocate(4 + 12 + encrypted.size).putInt(1).put(cipher.iv).put(encrypted).array()
      val output = file.startWrite()
      try { output.write(encoded); file.finishWrite(output) }
      catch (error: Exception) { file.failWrite(output); throw error }
    } finally { plain.fill(0) }
  }

  @Synchronized fun read(): String? {
    try {
      val bytes = try {
        file.openRead().use { input -> input.readBytesBounded(64 * 1024 + 32) }
      } catch (_: java.io.FileNotFoundException) { return null }
      require(bytes.size >= 32 && bytes.size <= 64 * 1024 + 32)
      val buffer = ByteBuffer.wrap(bytes)
      require(buffer.int == 1)
      val iv = ByteArray(12).also { buffer.get(it) }
      val encrypted = ByteArray(buffer.remaining()).also { buffer.get(it) }
      val cipher = Cipher.getInstance("AES/GCM/NoPadding")
      cipher.init(Cipher.DECRYPT_MODE, key(false) ?: throw GeneralSecurityException(), GCMParameterSpec(128, iv))
      cipher.updateAAD(aad)
      val plain = cipher.doFinal(encrypted)
      try { return plain.toString(Charsets.UTF_8).also { require(it.isNotEmpty()) } }
      finally { plain.fill(0) }
    } catch (_: GeneralSecurityException) {
      clear()
      throw IllegalStateException("credential_reauthorization_required")
    } catch (_: IllegalArgumentException) {
      clear()
      throw IllegalStateException("credential_reauthorization_required")
    }
  }

  @Synchronized fun clear() {
    file.delete()
    keystore().deleteEntry(alias)
  }

  internal fun removeKeyForVerification() { keystore().deleteEntry(alias) }
  internal fun ciphertextForVerification(): ByteArray = file.readFully()

  private fun java.io.InputStream.readBytesBounded(limit: Int): ByteArray {
    val output = java.io.ByteArrayOutputStream()
    val chunk = ByteArray(4096)
    while (true) {
      val count = read(chunk)
      if (count < 0) return output.toByteArray()
      if (output.size() + count > limit) throw IllegalArgumentException("credential_file_too_large")
      output.write(chunk, 0, count)
    }
  }
}
