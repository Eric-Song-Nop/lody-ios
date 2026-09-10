# Android navigation verification

Roadmap PR-05a. The implementation is on `codex/android-05a-navigation`, based on PR-04. Android product/account routes remain closed; this is an offline native navigation scene using the shared page and presentation contracts.

## Initial implementation and failure

Commit `4cc0936` introduced native tabs with project/settings stacks, Kotlin close control, platform-specific sheet/header options and an isolated Android Router context. Both TypeScript configurations, Android bundle and the internal APK build passed; shared presentation and session mailbox tests passed as well. `pnpm check` passed.

The first emulator round under `.artifacts/android/navigation-first/` failed before the bootstrap screen appeared. The screenshot is a blank native app surface. The saved tail log did not retain the startup error. Inspection of the installed Expo Router `getMostSpecific` implementation identified that every route must include a non-platform key; the selected context had only `.android.tsx` keys. Commit `824e3e9` maps the already-selected actual Android modules to normal Router keys. It does not provide fake route components or load unfinished iOS modules. The runner now captures logcat continuously from before app launch instead of retaining only a late tail. This fix requires a new emulator run.

## Remaining acceptance

The navigation runner covers project/session/message traversal, hardware system Back, sheet completion/cancellation, nested return and native close. A passing build alone does not establish these behaviors. Predictive back interruption, rapid navigation, complete teardown and theme/accessibility scenarios remain required before the full capability is accepted. Shared iOS UI regression and a normal-signing simulator build remain separate required checks.
