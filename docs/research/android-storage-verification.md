# Android storage verification

Date: 2026-09-10. Roadmap PR-04, [draft #5](https://github.com/Eric-Song-Nop/lody-ios/pull/5), based on PR-03 / draft #4. The storage APIs exist behind the Android kit facade; product account/catalog routes remain closed until PR-09.

## First local round

Commit `045a016` produced internal APK SHA-256 `e1d0ef4bd6fb90f0ddc1eaf084e73796115fe74a0546babaae4e3fdac2ead63d`. The dedicated Android 16 / API 36 ARM64 emulator passed all four `A-STORE-*` cases. Evidence is retained under `.artifacts/android/storage-first/` as result/storage JSON, before/after screenshots, video and logcat.

- Force-stop/relaunch changed PID 2527 to 3965; encrypted credentials and all 3,000,039 UTF-8 bytes of a Unicode stress projection survived.
- Restore took 322 ms in this round. This is an emulator measurement including credential verification, not a product cold-start or physical-device performance claim.
- Account/workspace selection restored only the appropriate projection.
- Deleting the actual fixture Keystore key produced the reauthorization error; a newly generated key subsequently saved/read a credential.
- Clear rejected the prior storage generation, removed the credential, and allowed recovery from malformed account JSON.

The ciphertext assertion uses a generated offline credential, never a real account token. Its hash is kept only in the private fixture store until clear. The evidence report contains no credential plaintext. Screenshots show the real native result; video shows preparation followed by a new application process.

## Integration strengthening

The first round tested storage with an independent stress fixture. It alone does not prove that a WASM-produced catalog is persisted and restored. The stronger storage flow first runs the actual eight-case WASM verifier, then writes its verified catalog through the same RN-to-native boundary as the shared catalog cache. After force-stop, it restores that catalog before starting any new WASM runtime. The separate large Unicode fixture still covers CursorWindow limits.

The stronger runner requires `seed-runtime.json` containing all eight real WASM passes and the actual verified catalog, plus `storage.json` with the restored catalog hash and distinct PIDs. This integrated round is pending; stage B must not be marked complete from the first storage round alone.

## Engineering and remaining gates

`pnpm check`, existing application/native-JS/tool tests, iOS bundle, generated Android backup configuration, and the full internal Android APK build pass. The full rebuild took 8m 11s, with 920 executed tasks. Native sources are in the single LodyKit module. See [the storage contract](../architecture/android-local-storage.md) for encryption, bounds, worker and generation ownership.

First-APK WASM/recovery/bootstrap regressions and a normal-signing iOS simulator build are being recorded separately. Updated Android integration assertions require a new APK and fresh evidence. Real login/logout UI, Cloud synchronization, background-service/OEM behavior and hardware-backed key attestation are not established here. Parent iOS UI CI failures remain separate from the local native/build gates. Remote acceptance publication is not claimed.
