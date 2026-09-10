# Android native menu verification

PR-05b remains [draft #7](https://github.com/Eric-Song-Nop/lody-ios/pull/7), stacked on PR-05a. This records a menu subset of A-UI-01; it does not complete PR-05b or stage C.

## Implementation

`NativeMenuButton` and `NativeContextMenu` now have Kotlin implementations registered in LodyKit. The Android entry exports these real views. The menu button preserves label, avatar, selected-item and action-ID props, measures its native label and enforces a 48 dp minimum through the shared wrapper. The context host observes long presses while preserving ordinary child taps and scrolling; when it opens a menu, it cancels the child's touch sequence.

The shared popup owner validates nonempty/unique action IDs and at most one selected item. It snapshots actions on opening, invalidates itself before dispatch, and dismisses on data replacement, anchor removal/hidden host or configuration changes. An old popup cannot dispatch through a replaced owner. This uses AppCompat PopupMenu 1.7.0, matching RN's existing dependency, to retain the project's API 24 minimum without calling the framework's newer force-icon API. Local emulator evidence is API 36 only.

A LodyKit theme overlay supplies blue selected controls in light/dark mode; filter entries use a native single-choice group. Dangerous context actions retain explicit titles and red text/icons. Source resources and Gradle dependencies live in LodyKit, not generated `apps/mobile/android` files.

## Offline behavior

`pnpm verify:android --case menus --appearance light|dark --apk <internal.apk>` opens the same production components in a regular page and a sheet. Each host verifies:

- Selecting a filter returns its exact ID once; reopening shows the correct checked row and unchecked alternative. System Back dismisses without another selection.
- Replacing filter data while its menu is open dismisses the old snapshot without an action.
- A short child tap increments the child counter; a long press opens context actions without another child tap. Selecting the destructive action returns its ID once.
- Removing the filter anchor while open dismisses its menu. Removing the context anchor while open separately dismisses its menu. Recreating both anchors allows a new valid selection without stale callbacks.

The scene uses local state and deterministic timers at the production-component boundary. It needs no login, Cloud or machine. The runner restores the original system night mode and releases its owned emulator.

## Evidence

Initial clean `2870d96` APK (`05371a2d5d88e8d16b69c74e28c2fa9815544cc1269d7b4938615ed18547e590`) passed touch assertions in both hosts. Static review failed because the default selected checkbox was green. `.artifacts/android/menus-first-light/visual-review.json` preserves that failure; automated success is not visual acceptance.

The revised clean `e242ddb` APK is `a70d71b00d35fb8f9da951b000e22a775fdfac76d134c7c4de3298becefb1707`. `.artifacts/android/menus-fixed-light/` passes both hosts, including the stronger per-row checked-state and both-anchor lifecycle checks. The 165.56-second recording is retained; sampled frames show no residual popup after anchor removal. Reviewed menu screenshots have blue single-choice controls and readable destructive titles. The same clean APK also passes both hosts in `.artifacts/android/menus-fixed-dark/`; its recording is 169.02 seconds. Both runs restore the previous night mode. Representative page/sheet menu screenshots and video samples at 15-second intervals were reviewed in both appearances; `visual-review.json` records the exact scope. A fresh normally signed iOS simulator build and strict signature verification pass; the original English home regression passes in light/dark (121.75/118.82 seconds). The verifier was then extended to open, select and cancel the actual LodyKit workspace menu, rather than only the adjacent toolbar view menu. Its first matcher incorrectly included the toolbar’s same-name StaticText after dismissal; the failed run is retained in `menus-workspace-home`. Matching the native menu Button and tapping its actual frame fixes the verifier. The expanded `menus-workspace-home-fixed` run passes light/dark (129.68/128.82 seconds); representative menu and restored-toolbar screenshots were reviewed, and the managed simulator was released.

`pnpm check`, `pnpm test`, `pnpm bundle`, Python compilation and the Android build pass. Logs are under `.artifacts/android/environment/menus-*.log`. CI status is independent of this local evidence, and local artifacts have not been published to a remote acceptance service.

## Remaining scope

Actual TalkBack navigation/actions and focus restoration, empty/disabled menus, live appearance changes while a popup is open, bilingual strings and broader system-font coverage still need explicit cases. UI Automator exposes the labeled native button and the labeled long-clickable context host; that alone is not TalkBack verification. Grouped lists, other system APIs and the final PR-05 navigation regression also remain. No refresh-rate, physical haptic or OEM behavior is claimed from this emulator.

## Edge-case follow-up in progress

Inspection of the Swift menu style found its single-line truncation and 200 pt width cap. The Android button now uses a 200 dp cap and single-line ellipsis, and empty menus use a disabled native button with reduced opacity. `menu-edges` adds a separate page/sheet fixture for long titles, density-adjusted dimensions, empty-menu behavior, appearance replacement while a popup is open, and keyboard open/back focus restoration. The Android build and static checks pass; emulator evidence for this follow-up is still pending; the existing menu evidence above belongs to the earlier APK.
