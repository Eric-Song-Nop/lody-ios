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

The case uses the real module's Expo lifecycle callbacks. It does not register fake implementations for unbuilt Cloud or UI capabilities. WASM is verified separately below; watchdog, storage and product fixtures arrive in their roadmap PRs.

**WASM case (PR-02)**

```sh
pnpm verify:android --case wasm \
  --apk apps/mobile/android/app/build/outputs/apk/release/app-release.apk
```

This opens the internal native verification screen and runs the real bundled data runtime in Kotlin's WebView. Fixture HTTP responses exercise normal Streams parsing and actual Flock/Loro WASM. Eight subcases cover incremental catalog updates plus Loro history, Zstd bootstrap, large projections, bridge output rejection, malformed frames/JSON and the catalog input ceiling. Each run stops every fixture runtime and requires zero HTTP writes. An absent subcase or failure is a failed run.

Artifacts add `runtime.json` (runtime/fixture hashes, structural projection checks, native bridge statistics) and `wasm-passed.png/xml`; the video is `wasm.mp4`. The implementation and bounds are described in `docs/architecture/android-data-runtime.md`. Native fixtures and expected projections are generated from the committed fixture source during `native:assets`; they contain no account data. Successful offline cases do not establish lifecycle recovery, authentication, or live Cloud access.

**Evidence limits**

This runner does not prove physical haptics, 120 Hz behavior, push delivery or OEM background policy. Separate device validation remains required in the roadmap. Acceptance service publication is additional to local artifacts; if the `lh` CLI is unavailable, retain artifacts and explicitly report publication as pending.

**Runtime recovery case (PR-03)**

```sh
pnpm verify:android --case recovery \
  --apk apps/mobile/android/app/build/outputs/apk/release/app-release.apk
```

The internal page runs the actual bundled WASM in real WebViews. The runner waits for the native readiness phase, presses Home, and returns to the Activity. Native lifecycle callbacks pause/resume the retained owner. An injected monotonic clock advances deadlines; ready/ping callbacks can be withheld at the native boundary. Renderer failure uses `WebViewRenderProcess.terminate()` on the API 36 baseline, rather than a fabricated success event.

`A-REC-01` through `A-REC-05` cover startup timeout, system background/foreground, heartbeat loss and bounded renderer recovery, stale generation callbacks, and stop without command replay. The report records state transitions, methods issued, all created/closed WebViews, restored session generations and HTTP write count. A negative `sendTurn` is issued once; this proves the supervisor does not replay commands, not the PR-10 durable dispatch/ACK-loss behavior. Real account, logout integration, background services and OEM behavior remain later-stage checks.

**Storage case (PR-04)**

```sh
pnpm verify:android --case storage \
  --apk apps/mobile/android/app/build/outputs/apk/release/app-release.apk
```

This case uses actual AndroidKeyStore encryption and SQLite with offline fixture data. The runner waits for `Storage prepared`, force-stops the app without clearing its data, launches a new process and resumes verification. The report must contain four `A-STORE-*` passes, different process IDs, and a projection larger than 2 MiB. Key loss is injected by deleting the real fixture key. The case also verifies account/workspace isolation, reauthorization, malformed saved context, and rejected old-generation writes after clear. See `docs/architecture/android-local-storage.md` for the ownership contract and product-integration limits.

When the dedicated emulator's background system services produce startup ANRs, `--settle-seconds 60` allows boot work to settle before installing the app and recording. The value is recorded in `result.json`; UI automation failures still fail the run. Do not mark an application case passed from this wait or disable system services to conceal a failure.

**Navigation case (PR-05a)**

`pnpm verify:android --case navigation --apk <internal.apk>` opens the Android-only Router graph from the runtime verification screen. NativeTabs own separate project/settings Stacks. The scenario opens project/session pages through the existing presentation/session mailbox, returns with the system Back key, completes and cancels sheets, returns from a nested sheet level and uses the Kotlin close button. It records message, nested-return and final-state screenshots plus video. The case requires no product account or cloud service. A runner implementation is not evidence that a build passed: follow the PR evidence record for the current result. Predictive-back cancellation, rapid navigation and final theme/accessibility coverage remain required before the full PR-05 capability is accepted.

`pnpm verify:android --case navigation-interruption --apk <internal.apk>` requires gesture navigation and verifies a committed edge return, three immediate open/return cycles and preservation of the project stack across tab switches. It also captures an attempted edge return-and-release, but page retention alone cannot establish that a predictive-back transition actually began. Fixture v2 reports only the `A-NAV-03-rapid-return` subset and records this gap explicitly; the v1 aggregate pass must not be interpreted as full A-NAV-03 acceptance. Teardown and active-transition cancellation remain separate required evidence.

Fixture v3 compiles `GestureInput.java` with JDK 17, SDK platform 36 and build-tools 36.0.0. The DEX runs as the adb shell user through `app_process` and uses the same input service entry as Android's `input` command; it is never included in the application. All events share a down time, move continuously away from the edge, hold for the preview screenshot, then return to the edge and release. `gesture-input.log` records injection readiness/release. Injection or capture timing failure fails the case. The preview image and video still require review to establish that the system recognized the gesture; a successful injection is insufficient by itself. The temporary device DEX is removed after the run. Set `JAVA_HOME` when the default JDK is not the build JDK.

`pnpm verify:android --case navigation-teardown --apk <internal.apk>` opens a sheet and inner page, then dismisses the entire Router host. The offline fixture observes real presentation IDs through the existing store, tracks pending presentation/inner results and mounted scene components, and displays their remaining counts on the runtime page. Two cycles must each end with zero mounted pages, zero pending results, no retained observed session and two cancelled results. Reset refuses to erase live state. These probes are imported only by the internal Android verification screens; they do not implement an alternate presentation store or modify product navigation.

Current navigation fixture v3 also exercises explicit cancellation, nested completion, downward sheet dismissal and both toolbar return targets; six outer results must settle once. Interruption fixture v4 additionally dismisses the navigation host after the five return cycles and requires every result and observed session to be released. See the evidence report for reviewed system-edge recognition/cancellation; the runner does not claim page-level predictive animation.

**Controls case (PR-05b, partial capability)**

`pnpm verify:android --case controls --appearance light --apk <internal.apk>` exercises LodyKit symbol/button/pressable/surface controls and the production shared text button in a regular page and a sheet. Use `--appearance dark` for the other starting appearance. It checks density-adjusted 48 dp bounds, single click/long-click results and disabled actions, then toggles system appearance without losing state. The original night-mode setting is restored in cleanup. This case does not yet cover menus, grouped lists, localization, TalkBack or physical haptics; follow [the control evidence record](../../../../docs/research/android-controls-verification.md) for actual results.

`pnpm verify:android --case menus --appearance light|dark --apk <internal.apk>` exercises the actual native filter menu and context menu in a page and a sheet. It checks selection IDs/counts and checked state, system-back cancellation, ordinary child taps versus long presses, destructive action dispatch, and removal/recreation of an anchor while its menu is open. Each host saves menu and final-state screenshots plus the shared recording. This touch-driven case does not establish TalkBack behavior or complete PR-05b acceptance.

`pnpm verify:android --case menu-edges --appearance light|dark --apk <internal.apk>` checks the native menu button with a long Chinese/English title, its 200 dp width cap and 48 dp touch target, empty-menu disabled state, appearance changes while a popup is open, and keyboard Tab/Enter/Back focus restoration in both hosts. Keyboard focus evidence is separate from TalkBack.
