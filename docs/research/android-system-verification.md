# Android clipboard, inbox preferences and selection feedback

PR-05b adds real LodyKit implementations of `copyText`, `selectionFeedback`, `initialInboxView`, `saveInboxView`, `readInboxExpansion` and `saveInboxExpansion`. This does not complete the system UI API inventory: toast and session-banner APIs are still outside the Android entry graph.

Clipboard writes use Android ClipboardManager and preserve the supplied text. No extra copy toast is shown. Selection feedback uses the foreground Activity's decor view on the main queue and requests platform CLOCK_TICK feedback without overriding system settings. A resolved call does not prove a physical vibration.

Inbox preferences use private SharedPreferences to preserve the existing synchronous facade. Writes check `commit()` and throw on failure. View indices follow the iOS normalization rule (1 or 0); project expansion stores independent boolean values and validates project IDs. These are app display preferences, matching the iOS owner, not credentials or account projections. The existing secure storage and catalog owners remain separate. `initialInboxView` is a launch-time value, not a live subscription.

The offline `--case system` scene uses production APIs. The runner saves preferences, force-stops and relaunches this app without clearing data, checks launch restoration and an independent project update, copies a Unicode/percent/brace fixture and pastes it through the system EditText menu. Haptic coverage checks only that the real API call resolves. Screenshots/video/results require review; physical and OEM behavior are not established by the emulator.

Implementation and local evidence are in progress. The first typecheck found a mistaken palette field in the new fixture; it was corrected to the existing `label` color role before emulator validation. No iOS implementation was changed.
