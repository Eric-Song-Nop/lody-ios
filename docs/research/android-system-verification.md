# Android clipboard, inbox preferences and selection feedback

PR-05b adds real LodyKit implementations of `copyText`, `selectionFeedback`, `initialInboxView`, `saveInboxView`, `readInboxExpansion` and `saveInboxExpansion`. This report covers that subset; subsequent toast and session-banner work is tracked in the separate [native feedback report](android-feedback-verification.md).

Clipboard writes use Android ClipboardManager and preserve the supplied text. No extra copy toast is shown. Selection feedback uses the foreground Activity's decor view on the main queue and requests platform CLOCK_TICK feedback without overriding system settings. A resolved call does not prove a physical vibration.

Inbox preferences use private SharedPreferences to preserve the existing synchronous facade. Writes check `commit()` and throw on failure. View indices follow the iOS normalization rule (1 or 0); project expansion stores independent boolean values and validates project IDs. These are app display preferences, matching the iOS owner, not credentials or account projections. The existing secure storage and catalog owners remain separate. `initialInboxView` is a launch-time value, not a live subscription.

The offline `--case system` scene uses production APIs. The runner saves preferences, force-stops and relaunches this app without clearing data, checks launch restoration and an independent project update, copies a Unicode/percent/brace fixture and pastes it through the system EditText paste key. Haptic coverage checks only that the real API call resolves. Screenshots/video/results require review; physical and OEM behavior are not established by the emulator.

The first typecheck found a mistaken palette field in the new fixture; it was corrected to the existing `label` color role before emulator validation. No iOS implementation was changed.

The first `72af43a` run (`system-first`) verifies preference restoration and isolated project updates, then stops because UI Automator does not expose the floating Paste toolbar visible in the screenshot. The revised runner focuses the EditText and injects Android KEYCODE_PASTE, exercising the platform clipboard read without setting the input from the fixture. The original failure is retained.

## Local evidence

The revised runner passes at `cdf96ff` in `.artifacts/android/system-paste-key/`, but visual review found the default teal cursor inconsistent with the UI baseline. `77145ec` supplies the existing blue accent to the fixture's cursor, selection and handle props. It does not change the platform clipboard or preference implementations.

The final `.artifacts/android/system-blue/` run passes `A-UI-01-system-preferences-clipboard` on clean commit `77145ec27a0ca452c87d90f8be5c2591bce2a363`, fixture `system-v1`, release-variant internal APK SHA-256 `aefc342b3acfd64b2b7346320d727e7f1394b71b66d4dedbeccfe1f8ea3b6fb9`. Environment: dedicated `Lody_Android_Verify_36`, API 36 ARM64, light appearance, adb port 5038, 60-second boot settlement. The runner shut down its owned emulator.

The four state screenshots were opened and reviewed: saved preferences, restored preferences after an independent project update, exact pasted text, and resolved feedback request. Text is readable, actions are blue and the final caret is blue. The 52.93-second recording was sampled across its duration at five-second intervals and reviewed alongside the state assertions. This scope does not establish selection-handle gestures, dark appearance, TalkBack, sheet haptics or physical vibration.

`pnpm check` and the incremental Android build pass after the fixture color change. The system API implementation also passed `pnpm test`, `pnpm bundle`, a normally signed iOS simulator build and strict deep signature verification; the later color change is confined to the Android Debug screen. Build/check logs are under `.artifacts/android/environment/system-*`; the iOS log is `.artifacts/android/ios-regression/system-build.log`.

This accepts only the listed system API subset. Toast/banner delivery is tracked separately; full PR-05b host/navigation/accessibility regression and stage C remain incomplete. Acceptance-service publication is pending because `lh` is unavailable; local artifacts are retained, not represented as uploaded evidence.
