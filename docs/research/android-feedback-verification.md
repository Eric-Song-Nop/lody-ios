# Android native toast and session banners

PR-05b implements `showToast`, `showSessionBanner` and `dismissSessionBanner` in the existing LodyKit module. This report tracks the implementation and pending local validation; it does not complete PR-05b or stage C.

## Ownership and platform behavior

`LodyFeedback` owns native Android views, timers and transient message state. A one-pixel `NativeFeedbackHost` marker registers each real page window through the existing presentation boundary, plus the Android root. The marker draws no feedback UI. The module chooses an attached, visible marker whose window has focus and attaches a native surface directly to that window's decor. There is no new bridge package, React Modal manager, remote script or permission to draw over other applications.

Toast cards appear at the bottom with system/IME inset clearance. Session banners appear at the top below system insets. Native TextViews use system text sizing, neutral surfaces and blue actions; warning/error text has corresponding semantic colors. Cards have an explicit close button of at least 48 dp and also dismiss when tapped. Empty surface areas pass touches to the owning page. Toast text displays up to four lines and banner text up to three; the accessibility label retains the full text. These are transient notices, not a replacement for detailed product error states.

Consecutive duplicate toasts reset their deadline; at most three notices remain. Completed banners expire, attention banners remain until dismissed or the app backgrounds. Replacing a banner replaces the old state. Unchanged native cards retain their views when other notices update. Moving between page and sheet windows migrates the surface while retaining deadlines; backgrounding clears notices and timers, and module destruction releases the host. No old notice is replayed on foreground.

The base timeout is 3.2 seconds for toasts and 4 seconds for completed banners. Android API 29+ uses the system's [recommended accessibility timeout](<https://developer.android.com/reference/android/view/accessibility/AccessibilityManager#getRecommendedTimeoutMillis(int,int)>); on older versions, touch exploration keeps timed notices dismissible without a short timeout. Native haptic requests respect system settings and do not establish physical feedback. `selectionFeedback` uses the active window marker when available.

The public void APIs validate kinds and enqueue the real native update on the main thread, preserving the existing request-style facade. They do not report delivery success. Empty messages are ignored, and requests made while backgrounded are not queued for later display.

## Offline behavioral scope

`pnpm verify:android --case feedback --feedback-host page --apk <internal.apk>` uses production APIs in a pushed page; repeat with `--feedback-host sheet` for a formSheet. Each host gets a separate recording within the recorder's 180-second limit. Planned assertions cover exact Unicode toast text, a bounded/coalesced burst, native expiry, persistent attention state, page touch pass-through, explicit dismissal, background cleanup and migration to the returning window. The runner records screenshots, UI hierarchy, video and the APK/source identity. Light/dark results and visual review must be recorded independently.

The initial `d51a82c` run (`feedback-first-light`) caught the info toast in the UI hierarchy, but its screenshot arrived after expiry; the later burst was missed entirely by the slow UI Automator observation. This is retained as failed/insufficient evidence. The revised runner temporarily sets Android's interactive accessibility timeout preference to 10 seconds so notices remain visible during hierarchy/screenshot capture; it restores and verifies the original preference in `finally`. The APK's base timers remain unchanged. Results must name this system preference and cannot be presented as default-duration visual evidence.

The initial compile caught a local `background` name shadowing a View property; the assignment now explicitly targets the ImageButton. Type checks, tests and iOS bundle pass; the corrected Android build passes. Emulator evidence and the shared presentation boundary's iOS UI regression are pending. Keyboard positioning, TalkBack announcements/focus, font coverage and physical haptics are not established by this initial scope.
