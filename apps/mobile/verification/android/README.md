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

**Native feedback (PR-05b)**

Run `--case feedback --feedback-host page` and `--case feedback --feedback-host sheet`, each with `--appearance light` and `--appearance dark`, using the same internal APK. Each invocation records one host so the flow stays within the 180-second screen recording limit. The case temporarily sets the real Android interactive accessibility timeout to 10 seconds, then restores and verifies the original value in `finally`; results identify this preference. It does not change the APK's default timers or prove default-duration visual timing.

The scene calls production LodyKit toast/banner APIs. It verifies Unicode text, at most three burst notices with consecutive duplicate coalescing, expiry, persistent attention, dismissal, page touch pass-through, background cleanup and migration to the returning window. Captures must visibly show the notice, not merely the underlying fixture after expiry. See `docs/research/android-feedback-verification.md` for source/APK identity, failures and remaining keyboard/accessibility/device coverage.

`--case feedback-keyboard` uses the same host and appearance arguments, opens a
real input and system keyboard, then checks native toast clearance, preserved
focus/draft and native close. System back must close the keyboard before the
page/sheet. This geometry/focus case uses a 60-second system interactive timeout
so slow IME startup and hierarchy capture do not erase the state being measured;
it restores the setting and does not test default expiry. Missing dispatch,
system IME frame, focus or notice fails the case. Screenshots and recordings
still need visual review. Results and remaining coverage are tracked in
[the feedback report](../../../../docs/research/android-feedback-verification.md).

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

### Native grouped list subset

`--case lists --appearance light|dark` runs production LodyKit grouped rows in
page and sheet hosts. It checks a 48 dp native row, action/static behavior,
stable-ID updates, navigation return, a real pull-to-refresh gesture, scrolling,
and empty/restore snapshots. Screenshots and the recording require visual review.
This subset does not establish TalkBack, arbitrary advanced iOS row features,
insert/delete anchor preservation or the complete PR-05 gate.

### Compiled language resources

`--case locales` compares every compiled native resource with the shared JSON
catalogs in English, Simplified Chinese and a fallback locale. It exercises
plural quantities 0/1/2, literal named interpolation and invalid inputs, and
captures rendered examples. Locale-specific Context resources are used; this
case does not establish whole-app language switching or TalkBack behavior.

### Runtime application language changes

The current fixture also requires translated native page titles and sheet close
labels. WindowManager appearance regions independently assert status-bar icon
contrast at each checkpoint; screenshots still require visual review.
Fixture v5 also consumes the production Inbox projection hook with stable catalog
inputs: section and badge copy must change language while the user title remains
literal. This checks projection-cache invalidation, not unsupported Android list
view fields or the unopened product Inbox route.

`--case locale-switch --locale-host page` uses real Android app locale overrides
(en-US → zh-Hans-CN → es-ES fallback → en-US), including a change while the app
is backgrounded. Run again with `--locale-host sheet` and repeat both with
`--appearance dark`. The runner restores the original override and appearance.
It requires API 33+ application locale shell support; absence is a failure, not
an in-app substitute. It checks independently subscribed memoized copy, native
close accessibility labels, editable draft/counter/process retention, and actual
route removal after dismissing any restored IME. Captures and recording remain
with the versioned result. This does not establish every product call site,
global device language settings, TalkBack speech or process-death draft recovery.

### Clipboard and display preferences

`--case talkback --talkback-host page|sheet --talkback-target controls|menus|lists`
uses the installed Google TalkBack service with real touch exploration. It requires
that service to bind, builds a shell-only API 36 hierarchy observer with JDK 17, performs touchscreen exploration/double-tap (and hold for
context menus), checks production action counts and system Back, and restores the
original accessibility settings in the runner’s `finally`. Hardware input uses the SDK's gRPC `sendTouch` on display 0, with one authenticated loopback connection and recorded event times. Exploration must focus the exact target without changing fixture text before activation. It records service/package state around every gesture, rechecking real binding
after hierarchy reads. TalkBack cases use one persistent shell-only `AccessibilityDump` connection with `FLAG_DONT_SUPPRESS_ACCESSIBILITY_SERVICES` for the entire run. Each snapshot clears the client cache without reconnecting the service. The observer records up to 512 focus/hover/window events in `accessibility-events.json`, with a dropped-event count; its Dex hash, request count and clean shutdown are recorded. Device accessibility settings are saved before observer registration and restored after it disconnects; its Dex is removed in cleanup. Observer failure fails the case, with no fallback to the default service-suppressing UI Automator dump;
The observer protocol has a local check: `python3 apps/mobile/verification/android/accessibility_observer_test.py`. This does not establish spoken-label quality or traversal order. Device gesture results and the still-incomplete host/theme matrix are recorded in the accessibility report. Before service activation, the internal fixture entry may be reached by at most five scrolls using observed container bounds. The first-run Android Accessibility Suite notification prompt is dismissed through TalkBack when its exact system resource IDs and message are present; unrelated tutorial overlays or failed activation still fail the case. The bound service label and enabled component are checked separately, and the last observed accessibility dump is retained on timeout.

TalkBack requires a runner-owned emulator; `--serial` is rejected for this case.
Install the isolated Python dependencies and invoke the runner with that Python:

```sh
python3 -m venv /tmp/lody-android-verification-python
/tmp/lody-android-verification-python/bin/pip install -r apps/mobile/verification/android/requirements-talkback.txt
/tmp/lody-android-verification-python/bin/python apps/mobile/verification/android/run.py \
  --case talkback --talkback-host page --talkback-target controls --appearance light \
  --apk apps/mobile/android/app/build/outputs/apk/release/app-release.apk
```

The runner generates protobuf bindings from the installed emulator's own `.proto`
into the evidence directory and records its hash. Authentication is read from the
exact owned process's discovery file, used only in RPC metadata and never copied
to results. Other cases require neither gRPC nor these Python dependencies, unless the explicit emulator screenshot option below is selected.

`--case list-focus --appearance light|dark` uses TAB, Enter, directional input
and system Back on production native rows. It requires repeated action updates
to retain keyboard focus and detail return to restore the navigation row's focus
in both page and sheet hosts. This is keyboard evidence, not TalkBack evidence.

`--case list-mutations --appearance light|dark` requires the fixture added in
`674cff2` or later. It scrolls into history, records a fully visible row's offset,
prepends/removes 20 rows above it, and requires the same row to retain that offset
and dispatch its current ID on both taps. Run both themes; each includes page and
sheet. It does not establish keyboard/TalkBack focus retention. The expanded list
fixture is `lists-v2` for the existing basic list case and needs a fresh APK;
older APKs cannot run the new mutation case.

`--case list-fonts --appearance light|dark` uses the production grouped list in
page and sheet hosts. It changes the real system `font_scale` from 1.0 to 1.3 and
back while the list is mounted, compares the long title's rendered height and row
bounds, retains the action counter/process, and checks Back dismissal. The prior
font setting is restored in `finally`, including an originally absent setting.
This is a native-list font check; it does not establish TalkBack speech, every
control's font behavior, or arbitrarily large accessibility layouts. Screenshots
and recording require separate visual review before acceptance.

`--case system` exercises the real LodyKit clipboard and inbox preference APIs.
It force-stops only the verification app to check persisted launch values, then
uses the Android EditText system Paste key to compare the complete clipboard fixture.
It also calls native selection feedback; this is not physical-haptic evidence.

### Semantic symbol corpus

`--case symbols --symbols-host page|sheet --appearance light|dark` requires the APK containing the 39-name
symbol fixture. It opens the production symbol views/buttons in the selected host (run both hosts separately),
captures all seven batches, checks 48 dp action targets and current action identity
after native view reuse, and returns through system Back. Review every captured
glyph pair and the recording for shape, contrast and variant semantics. The case
is implemented but has no device result yet; see
[the symbol report](../../../../docs/research/android-symbols-verification.md).

### Default toast timeout

`--case feedback-default --feedback-host page|sheet --appearance light|dark` uses the existing production feedback fixture with the system interactive timeout set to zero (no extension), restoring the previous value in `finally`. It requires accessibility services to be disabled; TalkBack behavior remains a separate case. It takes the visible screenshot before requesting another hierarchy dump, then checks absence after a six-second wait and actual Back dismissal. Capture latency and the observed absence time are recorded. Visual review must confirm the early screenshot contains the Unicode toast; the runner does not infer presence from a successful click or claim an exact 3.2-second measured lifetime. Run all four host/theme combinations. Current per-combination results and retained failures are recorded in the feedback evidence report.

The TalkBack fixture-menu search, before enabling the service, waits for observed text/bounds to remain unchanged for 500 ms after scrolling (five-second limit). Its geometry samples are retained in `fixtureEntryScrolls`. This replaces the old dump tool’s implicit idle wait; it does not retry taps or weaken exploration/action assertions.

`talkback-v3` explores with sustained hardware contact (450 ms) followed by four slow moves over 160 ms to the measured target center, then release; the path stays within eight pixels of that center. Every coordinate is retained. This replaces v2’s 150 ms stationary tap, which sometimes produced touch interaction without any hover. Double-tap/hold activation remains separate and exact focus/content/action checks remain mandatory.

`talkback-v4` retains v3 hardware gestures and additionally observes the popup's initial clickable accessibility focus and unchanged hierarchy for 500 ms, within a ten-second deadline, before exploring a menu item. Text visibility alone is insufficient: the retained page/light v3 failure assigned initial focus during the exploration and produced no target hover. Readiness samples are recorded in `popupFocusReadiness`; no focus action or gesture retry is used.

`feedback-default-v2` captures immediately after the synchronous input command, recording screenshot start and completion offsets. The two-second completion deadline and six-second absence check are unchanged. The earlier v1 page/light screenshot visibly contained the toast but missed the capture deadline at 2.062039 seconds; that failed run is retained. Product timing and system timeout settings are unchanged.

Default-toast screenshots additionally record first-byte, complete-PNG, and process-completion timing. The capture helper checks chunk checksums, complete output, process success and bounded receipt time, preserves original bytes, and leaves the existing two-second completion gate unchanged. Run its pipe-behavior checks with `python3 apps/mobile/verification/android/png_capture_test.py`. These timings diagnose capture latency; they do not measure when Android originally captured the displayed pixels.

`feedback-default-v3` adds `--screenshot-source emulator` for a runner-owned AVD. Invoke it with the isolated Python and gRPC dependencies above. It calls the installed SDK protocol's authenticated `getScreenshot` for display 0, omits scaling dimensions, writes the returned PNG without transforming pixels, and records dimensions, frame timestamp, protocol hash and host receipt/completion times. Inactive displays, wrong formats and mismatched PNG dimensions fail. Channels close before subsequent adb subprocesses. `--serial` and other cases reject this option; default `--screenshot-source adb` retains the original measured path. There is no automatic transport fallback or retry. The two-second deadline and production toast lifetime remain unchanged. Device results belong in the feedback report; adding this option alone does not establish acceptance.

`feedback-default-v4` schedules the single emulator screenshot at one second after input begins; the completion gate is still two seconds. The v3 immediate direct capture returned before the toast appeared and failed visual review despite passing programmatic checks. The adb path remains immediate. Retain both the PNG and recording: a successful capture or returned input command never establishes visible toast presence by itself.

`talkback-v5` adds explicit `--talkback-traversal` for `--talkback-target controls`. After the icon has actually gained focus and activated, four SDK hardware swipes require icon → disabled icon → text action → disabled icon → icon, using right/right/left/left. The gesture center comes from the display and current focus, never the next target. Each step records input coordinates/times and actual focus, captures a screenshot, and requires unchanged fixture content; focus is observed within five seconds, with no gesture retry or direct accessibility focus action. The original text-button activation and Back checks then continue. This bounded sequence does not establish full-screen reading order, spoken labels or originating-list-row focus restoration.

List TalkBack cases use `talkback-v7` and require the originating navigation row's
actual accessibility focus within five seconds after detail Back. The runner
records `listReturnFocus` and captures `talkback-list-return-focus` before any
further gesture. A correct return counter alone no longer passes this case.
Controls/menus retain v5; no direct focus assignment is used by the verifier.

For TalkBack lists and keyboard `list-focus-v2`, `--list-return removed|disabled`
changes the source row through a real detail-screen action before Back. `present`
is the default. Every keyboard variant, including ordinary `present` return,
must reach a real detail action with keyboard focus before Back. The runner records
`detailKeyboardFocus` for both hosts; it cannot pass by retaining focus on the
covered list. Ordinary return focuses the action without activating it.
Removal must remove the native row; disabling retains readable
content without navigation. Keyboard return must not restore either invalid
navigation target. TalkBack v7 observes the platform initial-focus property (API
34+ required by this observation) and rejects a stale return candidate. After
return, it uses real exploration/double-tap to select and increment another row,
then observes three seconds of focus continuity through the native list update.
This covers a new user selection after return, not every competing-focus race
during the transition. Each variant needs both hosts and its own evidence.

`--record-input-events` optionally records `getevent -lt` device timestamps during
an owned-emulator TalkBack run. RPC logs also include host send-start and return
times. The recording process is stopped in teardown; an early recorder exit
fails evidence collection. Use this to investigate a missed gesture without
changing gesture timings, retrying activation or assigning focus directly.

Every TalkBack hardware gesture is retained in `hardwareGestures` before focus
assertions. A single RPC or interval between events exceeding two seconds fails
with `hardwareGestureTimingError`: a host scheduling stall has invalidated the
planned input. This coarse guard exceeds the longest intentional 0.8-second hold;
it does not certify double-tap timing or replace device `getevent` evidence.
Invalid input still fails the run and never triggers an automatic gesture retry.

Exploration now observes exact focus for up to five seconds, matching the
traversal observation budget. Each observation is retained in
`talkBackExplorations[].focusObservations`; content changes still fail. This
replaces a fixed 0.8-second sample that could precede delayed TalkBack hover
processing. Input is sent once; the final target/subtree and hit bounds remain
mandatory.

TalkBack outer Back observes both the child body heading and its native toolbar
title disappearing, with the parent entry present for 500 ms. It retains
`parentReturnReadiness`; absence of scrolled-out body content alone does not
prove a sheet has finished dismissing. Review the returned capture and video
end separately before accepting the exit.
The accessibility hierarchy may hide a dismissing toolbar before its pixels
disappear. This observation window is not a native transition-completion signal;
an early returned screenshot or video end keeps exit acceptance incomplete.
