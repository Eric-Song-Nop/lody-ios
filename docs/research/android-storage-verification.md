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

The stronger runner requires `seed-runtime.json` containing all eight real WASM passes and the actual verified catalog, plus `storage.json` with the restored catalog hash and distinct PIDs. The first integrated run (`.artifacts/android/storage-integrated/`) reached the real WASM seed phase but exceeded the old 60-second preparation wait. Its failure screenshot, logcat and video are retained. The outer preparation wait now matches the standalone WASM case at 180 seconds; native per-case deadlines and behavioral assertions are unchanged. The next run (`.artifacts/android/storage-integrated-budget/`) failed before the case began: UI Automator exited 137, while logcat recorded ANRs in Google Play services and Digital Wellbeing. No storage assertion ran in that attempt. iOS simulators and prior Android emulators were confirmed stopped. A further run under `.artifacts/android/storage-integrated-settled/` records an explicit 60-second boot settling period before installation/recording; it also failed, with the final UI still at `Storage not run` and the 180-second recorder already stopped. The runner now records input coordinates and uses one stationary 100 ms touch so the press spans UI frames; it does not repeat actions or relax assertions. This input change and the startup-owner fix need fresh evidence. These failures remain failures, not app passes. Stage B must not be marked complete from the first storage round alone.

## Engineering and remaining gates

`pnpm check`, existing application/native-JS/tool tests, iOS bundle, generated Android backup configuration, and the full internal Android APK build pass. The full rebuild took 8m 11s, with 920 executed tasks. Native sources are in the single LodyKit module. See [the storage contract](../architecture/android-local-storage.md) for encryption, bounds, worker and generation ownership.

The first APK also passed eight WASM, five recovery and two bootstrap regression cases, under `.artifacts/android/wasm-storage-regression/`, `recovery-storage-regression/` and `bootstrap-storage-regression/`. All 14 iOS native behavior groups, the normal-signing simulator build and strict signature verification have also passed; see [the iOS regression record](ios-android-regression.md). Updated Android integration assertions require a new APK and fresh evidence. Real login/logout UI, Cloud synchronization, background-service/OEM behavior and hardware-backed key attestation are not established here. Parent iOS UI CI failures remain separate from the local native/build gates. Remote acceptance publication is not claimed.

## Integrated startup-owner round

The stronger flow passed on commit `cb6d3c5` with APK SHA-256 `6ccc1dec7de4686d28f66cf539ad20e97ae2a6283e6bbcce26f2550f664844e6`. Evidence is under `.artifacts/android/storage-startup-owner/`: all eight actual WASM seed cases passed, followed by all four storage cases. Process IDs changed from 3655 to 4597. The restored runtime catalog hash is `10db842e9f303efc688cd22a05ac687af28d93bcd5b1a7b1a9405915bdc921d3`; the separate Unicode fixture remains 3,000,039 bytes. Restore took 463 ms on this emulator, not a product performance guarantee.

The same APK passed all five recovery cases under `.artifacts/android/recovery-startup-owner/`, including startup suspension before readiness and actual renderer termination. The final screenshots and sampled video frames were visually reviewed. These new passes resolve the previously pending integration and startup-owner rerun; the failed earlier rounds remain retained. Physical SQLite corruption and backup/restore handling still require explicit coverage before all PR-04 storage requirements can be considered verified. The same-APK bootstrap regression passed both cases under `.artifacts/android/bootstrap-startup-owner/`; its run reports a dirty working tree because documentation was edited while the already-built APK was being verified.

## Additional storage boundary checks

Commit `3427152` adds actual missing-key restored-envelope and GCM tampering checks, inspects the installed application backup flag, and corrupts the isolated fixture SQLite file before testing failure and explicit clear/recreation. The runner requires each boundary result individually. These additions need a fresh APK and emulator pass; they do not inherit the earlier integration result. The envelope scenario models transferred ciphertext without its non-exportable key; it does not claim an OEM backup transport has been exercised.

The boundary round under `.artifacts/android/storage-boundaries/` failed at the corrupt-database assertion. Logcat shows `DefaultDatabaseErrorHandler` deleting the fixture database during startup. The default open operation could therefore return an empty replacement rather than expose a restoration failure. Commit `4780808` installs a corruption handler that throws without deleting the file; only explicit `clear()` performs database deletion/recreation. The scenario now also requires the corrupted file to survive and a second read to fail before clear. This fix requires its own fresh emulator run.

## Corruption fix verified

The fixed internal APK (`1ddca682aab8b31bac931c0d490dde3ec632133cd161c579f1bca4ae696149c1`) passed the complete strengthened storage flow at clean commit `75df49d`. `.artifacts/android/storage-corruption-fixed/` retains all eight WASM seed passes, all four storage cases, screenshots, video and logs. The report explicitly confirms rejection of restored envelopes without keys and tampered GCM envelopes, installed backup disabling, and actual corrupt database failure followed by explicit recovery. The fixture file survived two failed reads before clear; a new account could then be saved and restored.

Process IDs changed 3709→4581, the actual runtime catalog hash remained `10db842e9f303efc688cd22a05ac687af28d93bcd5b1a7b1a9405915bdc921d3`, and the separate 3,000,039-byte Unicode projection was intact. Restore measured 1,270 ms on this emulator; this does not establish a cold-start performance budget. Sampled video frames were reviewed. `pnpm check` passed after the fix. Same-APK recovery/bootstrap regression is in progress; prior iOS native/build inputs are unchanged. OEM transfer behavior and product auth/logout flows remain separately scoped.

## Final same-APK stage B regression

The final APK `1ddca682aab8b31bac931c0d490dde3ec632133cd161c579f1bca4ae696149c1` also passed all five runtime recovery cases and both bootstrap cases in `.artifacts/android/recovery-storage-final/` and `.artifacts/android/bootstrap-storage-final/`. Combined with the eight actual WASM seed cases and four strengthened storage cases, this is 19 local emulator checks on the final binary. Final screenshots were reviewed. This completes the local stage B native data/storage gate; remote CI, real product integration and release gates remain separate. The runner records checkout commits separately from the APK hash; documentation-only commits during the sequence did not rebuild the APK.
