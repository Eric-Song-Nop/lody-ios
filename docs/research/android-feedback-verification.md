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

This is a bounded feedback subset, not complete PR-05b acceptance. Keyboard, system-font and TalkBack coverage remain required; video sampling does not establish frame-rate or physical haptic performance. Local artifacts have not been published through `lh`, which is unavailable on this host.

## iOS offline fixture correction

The normally signed iOS simulator build and strict signature check passed. An initial UI invocation could not find AXe; the rerun used the installed AXe binary. The `feedback-home-path` light/dark scenarios then passed their automated assertions, but visual review caught a `not_ready` runtime error toast in the new-session sheet. The offline home fixture was still calling the real creation-options loader.

Commit `6e8339c` injects creation options through the existing screen service boundary and adds a check rejecting that runtime-error state. Production loading retains its existing path; no fake native success API was introduced. The repaired `feedback-home-isolated` run passed both home scenarios (light 128.91 s, dark 126.34 s), recorded from clean `cc8e7b5` with AXe 1.8.0 and Xcode 26.5. The four compact/full new-session screenshots were reviewed: the runtime-error toast is absent and the native composer and controls remain visible. This visual review specifically covers the fixture repair; it does not claim a new full iOS visual acceptance. The managed simulator lease was released after the run. The prior failed visual evidence remains in place.

## Keyboard follow-up

The separate `feedback-keyboard` case opens a real TextInput and system IME, requests the production toast, compares its native bounds with the visible keyboard, and checks that focus and draft text survive. Native close must leave the keyboard open; system back must dismiss the keyboard before closing the host. Run separately for page/sheet and each appearance. This fixture and runner are implemented; emulator results are pending.
