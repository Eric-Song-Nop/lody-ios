# Android native toast and session banners

PR-05b implements `showToast`, `showSessionBanner` and `dismissSessionBanner` in the existing LodyKit module. This report tracks the implementation and local validation; it does not complete PR-05b or stage C.

## Ownership and platform behavior

`LodyFeedback` owns native Android views, timers and transient message state. A one-pixel `NativeFeedbackHost` marker registers each real page window through the existing presentation boundary, plus the Android root. The marker draws no feedback UI. The module chooses an attached, visible marker whose window has focus and attaches a native surface directly to that window's decor. There is no new bridge package, React Modal manager, remote script or permission to draw over other applications.

Toast cards appear at the bottom with system/IME inset clearance. Session banners appear below the active page’s native header, using the marker’s content origin in that window and system insets. Activity and Dialog coordinates are converted within their own window. Native TextViews use system text sizing, neutral surfaces and blue actions; warning/error text has corresponding semantic colors. Cards have an explicit close button of at least 48 dp and also dismiss when tapped. Empty surface areas pass touches to the owning page. Toast text displays up to four lines and banner text up to three; the accessibility label retains the full text. These are transient notices, not a replacement for detailed product error states.

Consecutive duplicate toasts reset their deadline; at most three notices remain. Completed banners expire, attention banners remain until dismissed or the app backgrounds. Replacing a banner replaces the old state. Unchanged native cards retain their views when other notices update. Moving between page and sheet windows migrates the surface while retaining deadlines; backgrounding clears notices and timers, and module destruction releases the host. No old notice is replayed on foreground.

The base timeout is 3.2 seconds for toasts and 4 seconds for completed banners. Android API 29+ uses the system's [recommended accessibility timeout](<https://developer.android.com/reference/android/view/accessibility/AccessibilityManager#getRecommendedTimeoutMillis(int,int)>); on older versions, touch exploration keeps timed notices dismissible without a short timeout. Native haptic requests respect system settings and do not establish physical feedback. `selectionFeedback` uses the active window marker when available.

The public void APIs validate kinds and enqueue the real native update on the main thread, preserving the existing request-style facade. They do not report delivery success. Empty messages are ignored, and requests made while backgrounded are not queued for later display.

## Offline behavioral scope

`pnpm verify:android --case feedback --feedback-host page --apk <internal.apk>` uses production APIs in a pushed page; repeat with `--feedback-host sheet` for a formSheet. Each host gets a separate recording within the recorder's 180-second limit. Assertions cover exact Unicode toast text, a bounded/coalesced burst, native expiry, persistent attention state, page touch pass-through, explicit dismissal, background cleanup and migration to the returning window. The runner records screenshots, UI hierarchy, video and the APK/source identity. Light/dark results and visual review must be recorded independently.

The initial `d51a82c` run (`feedback-first-light`) caught the info toast in the UI hierarchy, but its screenshot arrived after expiry; the later burst was missed entirely by the slow UI Automator observation. This is retained as failed/insufficient evidence. The revised runner temporarily sets Android's interactive accessibility timeout preference to 10 seconds so notices remain visible during hierarchy/screenshot capture; it restores and verifies the original preference in `finally`. The APK's base timers remain unchanged. Results must name this system preference and cannot be presented as default-duration visual evidence.

The initial compile caught a local `background` name shadowing a View property; the assignment now explicitly targets the ImageButton. Type checks, tests and iOS bundle pass; the corrected Android build passes. The emulator matrix below passes; the shared presentation boundary’s iOS home scenarios pass after correcting their offline fixture. Keyboard positioning, TalkBack announcements/focus, font coverage and physical haptics are not established by this initial scope.

## Header-clearance repair and emulator matrix

The earlier `feedback-vector-*` matrix passed its behavioral assertions but failed visual review: banners overlaid native page/sheet titles. Those results and rejection records remain available. Commits `7293072` and `d3184ec` use the native page content origin and add an explicit header-clearance assertion. The corrected matrix uses the same release APK, SHA-256 `6a7f5304da1e0b8e5be4e8fc4c30f7ea6c6f0873f79ac988feefa7821917884a`, built from clean `d3184ec`, on the dedicated API 36 arm64 emulator.

| Local artifact directory under `.artifacts/android/` | Recording duration | Result                          |
| ---------------------------------------------------- | ------------------ | ------------------------------- |
| `feedback-header-page-light`                         | 109.23 s           | Behavior and visual review pass |
| `feedback-header-sheet-light`                        | 110.33 s           | Behavior and visual review pass |
| `feedback-header-page-dark`                          | 123.24 s           | Behavior and visual review pass |
| `feedback-header-sheet-dark`                         | 114.51 s           | Behavior and visual review pass |

All 20 notice-state screenshots were opened and reviewed, together with samples spanning each full recording. Native headers remain visible, text and close actions are readable in both appearances, toast bursts are bounded to three cards, and the returning window owns the surviving banner. Every run restored the interactive accessibility timeout preference and night mode. The first three runs recorded clean `d3184ec`; the final run’s source identity is retained in its result file (documentation changed during the matrix, with no APK change). The matrix shut down its own emulator before starting iOS verification.

This is a bounded feedback subset, not complete PR-05b acceptance. Keyboard coverage is recorded separately below; system-font and TalkBack coverage remain required; video sampling does not establish frame-rate or physical haptic performance. Local artifacts have not been published through `lh`, which is unavailable on this host.

## iOS offline fixture correction

The normally signed iOS simulator build and strict signature check passed. An initial UI invocation could not find AXe; the rerun used the installed AXe binary. The `feedback-home-path` light/dark scenarios then passed their automated assertions, but visual review caught a `not_ready` runtime error toast in the new-session sheet. The offline home fixture was still calling the real creation-options loader.

Commit `6e8339c` injects creation options through the existing screen service boundary and adds a check rejecting that runtime-error state. Production loading retains its existing path; no fake native success API was introduced. The repaired `feedback-home-isolated` run passed both home scenarios (light 128.91 s, dark 126.34 s), recorded from clean `cc8e7b5` with AXe 1.8.0 and Xcode 26.5. The four compact/full new-session screenshots were reviewed: the runtime-error toast is absent and the native composer and controls remain visible. This visual review specifically covers the fixture repair; it does not claim a new full iOS visual acceptance. The managed simulator lease was released after the run. The prior failed visual evidence remains in place.

## Keyboard follow-up

The separate `feedback-keyboard` case opens a real TextInput and system IME, requests the production toast, compares its native bounds with the visible keyboard, and checks that focus and draft text survive. Native close must leave the keyboard open; system back must dismiss the keyboard before closing the host. Run separately for page/sheet and each appearance. The fixture and runner pass the emulator matrix below.

The first keyboard run (`feedback-keyboard-first-page`, clean `8e8b89f`, APK `e2d0d2d04c53dc9b838277c9f909756e2531c3d6a99f33a700f285badda086d1`) failed to observe the transient toast during a slow first IME startup. Its log contains input-method timeouts and system delays; this does not prove why the toast was missed. The follow-up fixture counts actual public API requests and captures IME readiness and the requested state. The geometry/focus case now uses the real system 60-second interactive timeout, restores it afterward and makes no expiry claim.

The observed rerun (`feedback-keyboard-observed-page-light`, clean `8368e1a`, APK `22cfe0e8764d05a0ee137e42473353b402edf96e6d736a6f95b1d07c6cca9999`) visibly showed the native toast above the keyboard with the input caret retained. It failed because UI Automator’s active-window hierarchy omitted the separate keyboard window. The v2 verifier obtains the visible IME frame from `dumpsys window displays`, records the raw system report, and rejects missing or ambiguous frames. This checks the app’s card against independently reported system geometry. The repaired matrix passes below; both earlier failures remain retained.

### Keyboard matrix result

The same APK `22cfe0e8764d05a0ee137e42473353b402edf96e6d736a6f95b1d07c6cca9999` (fixture code from `b818853`) passes all four cases on the dedicated API 36 arm64 emulator:

| Local directory under `.artifacts/android/` | Runner commit / worktree       | Video   | Result                          |
| ------------------------------------------- | ------------------------------ | ------- | ------------------------------- |
| `feedback-keyboard-window-page-light`       | `704f09c`, clean at start      | 35.50 s | Behavior and visual review pass |
| `feedback-keyboard-window-sheet-light`      | `83cf827`, documentation dirty | 37.75 s | Behavior and visual review pass |
| `feedback-keyboard-window-page-dark`        | `9cfbf29`, clean               | 35.34 s | Behavior and visual review pass |
| `feedback-keyboard-window-sheet-dark`       | `9cfbf29`, clean               | 38.33 s | Behavior and visual review pass |

All 16 readiness/requested/visible/dismissed screenshots and full-recording five-second samples were reviewed. The immediate requested capture can precede native rendering; the separate visible capture and geometry assertion establish display. The native toast bottom is 1,475 px and the independent system IME starts at 1,517 px in this device configuration. Draft text and focus survive the request, native close leaves the IME open, and system back closes IME before the page/sheet. Every run restores the system interactive-timeout preference and night mode. The matrix shuts down only its owned emulator.

No native implementation change was needed for this keyboard result. The new Debug screen uses the production feedback API and TextInput; verification corrections address slow observation and the separate keyboard window. `pnpm check` and the updated Android release build pass. The keyboard-only Android fixture does not change the iOS entry graph. This does not replace PR-08 composer/IME composition tests, nor complete PR-05b’s language, font, TalkBack, dynamic list or final navigation requirements.

Default-timeout verification was first run on APK `553d7744…` using `feedback-default-page-light-v1`. It failed the two-second capture deadline at 2.062039 seconds, before expiry/Back assertions. The individually reviewed early screenshot does show the Unicode toast; original timeout restores to `null`. This remains a failed case, not full default-duration evidence. The v2 verifier removes the extra 300 ms sleep between the synchronous input command and screenshot, records capture start as well as completion, and retains the two-second deadline and six-second absence check. Product timeout is unchanged. The v2 page/light run exits zero on the same APK: capture starts at 0.234339 seconds and finishes at 1.859767 seconds; absence is observed after the six-second wait and hierarchy read at 8.849766 seconds. All five PNGs and five-second samples across 34.165711 seconds were reviewed. The Unicode toast is visibly readable and clears the system gesture area, later disappears, Back returns to Projects, and original timeout restores to `null`. This proves appearance and later expiry under an unextended timeout, not exact 3.2-second duration. Other host/theme combinations remain pending. Runner source is `892799c` plus the v2 capture change.

The next v2 sheet/light attempt stops at the capture deadline: screenshot starts at 0.201150 seconds but the PNG command completes at 2.049075 seconds. Its individually reviewed screenshot visibly contains the correctly positioned Unicode toast; the command duration, rather than missing visual content, triggers this failure. Expiry and Back assertions do not execute; original timeout restores to `null`. The batch stops before either dark case. Removing the pre-capture sleep alone is insufficient to make this capture deadline reliable; capture latency needs investigation before claiming the remaining default-timeout matrix.
