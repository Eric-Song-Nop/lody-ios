# Android offline verification

PR-01 provides an internal bootstrap entry with the actual Kotlin LodyKit module. Product routes are introduced by later roadmap PRs. No Cloud account, network fixture, desktop credentials or connected machine is required for the bootstrap case.

**Requirements**

Use JDK 17 and the SDK versions resolved by the pinned Expo/RN dependencies. Current RN/Expo native defaults are minSdk 24 and compile/target SDK 36. The generated Expo project uses Gradle 9.3.1. `withAndroidBuild` persists 4 GiB heap, 2 GiB metaspace and four Gradle workers after the default 512 MiB metaspace failed during Expo Updates KSP. The build targets `:app:assembleRelease` rather than also assembling every library; generated files are not the configuration source. Set `ANDROID_HOME` to your SDK (on macOS the build helper defaults to `~/Library/Android/sdk`).

Create a dedicated verification AVD once, with the installed matching image:

```sh
"$ANDROID_HOME/cmdline-tools/latest/bin/avdmanager" create avd \
  --name Lody_Android_Verify_36 \
  --package 'system-images;android-36;google_apis_playstore;arm64-v8a' \
  --device pixel_7
```

The runner checks both `~/.android/avd` and `~/.config/.android/avd` for its named AVD, then explicitly passes the registry to the emulator. Set `--avd-home` if the name is missing or ambiguous; it respects an existing `ANDROID_AVD_HOME`. This handles different SDK tool defaults without moving user AVDs.

Do not use `--force` against an existing AVD or erase a user's emulator. CI on x86 hosts needs a matching x86 image and an explicit AVD name.

**Build and run**

```sh
pnpm prebuild:android
pnpm bundle:android
pnpm build:android
pnpm verify:android --case bootstrap \
  --apk apps/mobile/android/app/build/outputs/apk/release/app-release.apk
```

The release variant currently uses Expo's generated development signing key for internal testing only. It is not a production signing configuration. `build:android` embeds the internal entry and disables OTA for that build using `EXPO_PUBLIC_ANDROID_VERIFY=1`. `pnpm android` starts the same internal entry in a developer build. Android builds without this explicit internal flag reject the unavailable product entry.

Verification uses the SDK adb server on port 5038 (`--adb-port` overrides it), leaving any user service on port 5037 untouched. This avoids older adb servers bundled with phone connection apps.

The default GPU mode is `host` on this local Mac; override `--gpu auto` or `--gpu software` for another environment. Owned emulators receive 4096 MiB RAM (`--memory-mb` overrides it) without changing the saved AVD configuration. The initial lower-memory API 36 runs produced system-UI ANRs with both software and host rendering; these are recorded as environment failures, not application passes. Avoid running memory-heavy native builds during emulator acceptance on limited-memory hosts.

The runner starts the named dedicated AVD on a free emulator port, waits for boot, installs the supplied APK, clears only `app.innei.lody`, and shuts down only the emulator it started. With `--serial`, the caller owns device startup/shutdown and authorizes installation and app-data reset. Do not target a user's signed-in installation. No device-wide wipe is performed.

Outputs default to `.artifacts/android/<timestamp>/`: `result.json`, UI hierarchy XML, PNG screenshots, a screen recording and logcat. An existing output directory is rejected to avoid overwriting evidence. Supply `--output` for an explicit new directory. Unknown/missing cases, timeouts, assertion failures and missing video fail the command. Review screenshots/video visually before claiming acceptance; programmatic assertions alone only establish the recorded behavior.

**Bootstrap case**

- `A-BOOT-01`: open the offline entry and show actual Kotlin system/version constants, proving the module is registered and callable.
- `A-BOOT-02`: background and return while subscribed, observe one native foreground event, detach, then background and return again; the counter must remain unchanged. The component also removes subscriptions during unmount.

The case uses the real module's Expo lifecycle callbacks. It does not register fake implementations for unbuilt Cloud or UI capabilities. WASM, watchdog, storage and product fixtures arrive in their roadmap PRs; they are not claimed by bootstrap.

**Evidence limits**

This runner does not prove physical haptics, 120 Hz behavior, push delivery or OEM background policy. Separate device validation remains required in the roadmap. Acceptance service publication is additional to local artifacts; if the `lh` CLI is unavailable, retain artifacts and explicitly report publication as pending.
