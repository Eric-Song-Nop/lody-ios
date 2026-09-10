# Android navigation verification

Roadmap PR-05a, [draft #6](https://github.com/Eric-Song-Nop/lody-ios/pull/6), stacked on #5. The implementation is on `codex/android-05a-navigation`, based on PR-04. Android product/account routes remain closed; this is an offline native navigation scene using the shared page and presentation contracts.

## Initial implementation and failure

Commit `4cc0936` introduced native tabs with project/settings stacks, Kotlin close control, platform-specific sheet/header options and an isolated Android Router context. Both TypeScript configurations, Android bundle and the internal APK build passed; shared presentation and session mailbox tests passed as well. `pnpm check` passed.

The first emulator round under `.artifacts/android/navigation-first/` failed before the bootstrap screen appeared. The screenshot is a blank native app surface. The saved tail log did not retain the startup error. Inspection of the installed Expo Router `getMostSpecific` implementation identified that every route must include a non-platform key; the selected context had only `.android.tsx` keys. Commit `824e3e9` maps the already-selected actual Android modules to normal Router keys. It does not provide fake route components or load unfinished iOS modules. The runner now captures logcat continuously from before app launch instead of retaining only a late tail. This fix requires a new emulator run.

## Remaining acceptance

The navigation runner covers project/session/message traversal, hardware system Back, sheet completion/cancellation, nested return and native close. A passing build alone does not establish these behaviors. Predictive back interruption, rapid navigation, complete teardown and theme/accessibility scenarios remain required before the full capability is accepted. Shared iOS UI regression and a normal-signing simulator build remain separate required checks.

## Router fix and nested system Back

The normalized route graph loads on the actual emulator. `.artifacts/android/navigation-route-keys/` passed project→sessions→messages and system return, then completed a form sheet and cancelled a page sheet. It failed after pushing an inner sheet page: system Back cancelled the entire outer sheet instead of returning to its parent page. The final video frame shows Settings with the third outer sheet already cancelled. The local ScreenStack levels were not represented in Router's outer navigation state.

The fix adds a focus-scoped Android BackHandler only while the sheet has inner levels. It cancels the top inner level and consumes that committed Back event; an empty inner stack lets Router dismiss the outer sheet. iOS does not install this handler. The runner cleanup was also corrected so failure screenshots remain captured and its continuous startup log is not overwritten by a late log tail. Fresh behavior verification is required. The iOS production bundle and the four existing presentation/session-mailbox behavior tests passed before this follow-up.
