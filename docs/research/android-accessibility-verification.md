# Android TalkBack verification

PR-05b remains incomplete. The runner uses the installed Google TalkBack service and records actual native action counts after touchscreen exploration and double-tap. It does not establish spoken-label quality, traversal order or complete accessibility coverage.

## Retained failures

Both attempts used API 36 ARM64 and APK `3382ae3edf3f4ebd1c53236af449bcc99a3c7f7b31873adb51ceb0cd590a9d38`, controls/page/light:

- `.artifacts/android/talkback-controls-page-light`: the fixture entry was outside the visible ScrollView and the runner raised `StopIteration` before enabling TalkBack. No control action was tested.
- `.artifacts/android/talkback-controls-page-light-entry-scroll`: one observed-bounds scroll reached the production controls page. The run then timed out in its bound-service predicate. The reviewed failure screenshot and hierarchy show Android Accessibility Suite's notification permission prompt over the native controls, with the TalkBack focus border. Original accessibility settings were restored and the owned emulator stopped. This screenshot does not prove the action test passed.

## Prepared correction and limits

The fixture search is bounded to five scrolls before enabling TalkBack. Product action lookup remains strict. The service predicate now distinguishes the bound service label from the enabled component, and retains its final observed dump on failure. Android's [service connection dump](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/services/accessibility/java/com/android/server/accessibility/AbstractAccessibilityServiceConnection.java) emits the label; [user-state dumping](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/services/accessibility/java/com/android/server/accessibility/AccessibilityUserState.java) emits enabled components separately. The old predicate incorrectly required `TalkBackService` in the label section.

The observed screen-reader notification prompt is handled by its exact permission-controller resource IDs and Android Accessibility Suite message, using the same real TalkBack gesture path. Other onboarding overlays still fail readiness. This correction has Python syntax validation only so far; real activation, prompt dismissal and the full page/sheet × light/dark × controls/menus/lists matrix remain unverified.

## Service predicate verified; gesture correction in progress

The `service-label` attempt on the same APK confirms a real bound `Service[label=TalkBack,…]`, the enabled full component and `touchExplorationEnabled=true`. It then fails fixture readiness: the reviewed failure screenshot still shows the notification permission prompt after the attempted double tap. Original accessibility settings were restored; no control activation passed. The old `talkBackNotificationPromptDismissed` field was set immediately after input in that failed artifact and is not evidence of dismissal. It is now recorded only after fixture readiness succeeds.

A shell-only `TalkBackInput` driver now sends exploration and both taps inside one device process, recording actual MotionEvent times; it is not bundled in the app. This removes separate adb/process startup delays between taps. Service checks before and after remain required, as do actual prompt removal and native action counts. The new run is pending; the remaining cause could still involve service rebinding after UI Automator snapshots. No timing-only change is treated as accessibility acceptance.
