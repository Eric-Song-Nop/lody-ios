# Android system controls verification

Roadmap PR-05b ([draft #7](https://github.com/Eric-Song-Nop/lody-ios/pull/7)) is being implemented on `codex/android-05b-system-controls`, stacked on PR-05a (`codex/android-05a-navigation`, draft #6). This record describes the first control cohort, not completion of PR-05b or stage C.

## Implemented first cohort

- Kotlin `LodySymbolView`, `LodySymbolButton`, `LodyPressable` and `LodyGlassSurface` are registered through the existing LodyKit module. Symbol buttons use native click/long-click semantics, disabled state, ripple and 48 dp minimum bounds. The glass facade uses an ordinary opaque Android surface.
- NativeTabs now use licensed Material folder/settings resources for selected and unselected states. The current semantic mapping covers the internal scene only; unknown symbol names are rejected and product screens must add their actual mappings before entering the Android graph.
- Android `usePalette` resolves system text color resources and uses blue actions with neutral backgrounds. Android `AppText` uses the system font and native font scaling, without the iOS clamp or Menlo font name. The original iOS implementations remain the default files.
- The shared production `Button` is exercised through its actual native pressable/surface components in a regular page and a sheet. The wrapper enforces 48 dp Android minimums even when a caller requests the former 44 pt size.
- Material SVG sources, source URLs/hashes, an offline VectorDrawable converter and Apache-2.0 text are committed. Gradle includes the native license directory in the Android assets; the common license index includes Material Symbols.

## Behavioral cases

`pnpm verify:android --case controls --appearance light|dark --apk <internal.apk>` drives both hosts. It measures the native icon target against device density, checks click versus long-click counts, verifies disabled controls emit no actions, and taps the shared text button. It changes system appearance while each host is open and requires the existing count to survive, then returns to the requested appearance. The runner restores the original system night-mode setting during cleanup, including failed runs.

Each host emits an `A-UI-01-controls-*` subset result. Screenshots and video require review for icons, text contrast, ripple/surface layout and theme changes. These assertions do not establish TalkBack behavior or physical haptics.

## Current evidence and remaining work

`342d4bf` contains the first cohort; `b8fa5d3` adds native license packaging. `pnpm check` passes, including both TypeScript configurations, locale checks, generated licenses and formatting. Python compilation and local SVG conversion pass. The Android build passes; the follow-up license build also passes and the APK license entry matches the source text byte-for-byte. The repeat emulator evidence below supersedes the initial visual failure for this subset.

PR-05b still requires native menus/context actions, grouped rows and their selection behavior, the remaining system APIs and semantic icons, generated Android strings/plurals, Chinese/English coverage, TalkBack and the final shared-host/iOS regressions. Those capabilities are not exported as placeholder native APIs.

## First emulator round: behavior passes, visual acceptance fails

The first APK (`14f8f94651cb46d9cecc737a1b7e12a5bb7cecdd0c0630f6ecebded9ed56afa3`, clean `937c4b6`) passes automated click/long-click/disabled-state checks in both hosts and measures both icon targets at 48 dp. The runner restores night mode successfully. However, reviewed screenshots under `.artifacts/android/controls-first-light/` show invisible body text, missing/misplaced button surface layout and dark header/close colors after switching to dark mode. `visual-review.json` records failure; the automated pass is not UI acceptance.

Inspection of the installed RN converter shows that theme-attribute resolution returns `TypedValue.data`; for the text ColorStateList attributes that value is a resource ID, not ARGB. Android palette colors now use system color resource paths, which resolve through `ResourcesCompat.getColor`. The native pressable now leaves measurement/layout of RN children to Yoga instead of LinearLayout. Sheet title/back colors and the native close control are refreshed for appearance changes. A new APK and repeat visual/behavior evidence are required.

## Repeat emulator round after visual fixes

Clean `44ba05a`, APK SHA-256 `bcff5951425d1b02837dcc1b0872509373ea06f36618446e6584af521fe1bece`, passes both `controls` runs starting in light and dark appearance on the dedicated API 36 ARM64 emulator. Evidence is retained in `.artifacts/android/controls-visual-fixed-light/` and `.artifacts/android/controls-visual-fixed-dark/`. Each run checks the regular page and sheet, including an appearance change without losing action counts. Both icon targets measure 48 dp; both runners restore the previous night-mode setting.

All eight state screenshots were reviewed. Body text is visible, the production text button has its background and centered label, and the sheet title/back/close controls and status bar adapt in both directions. Static visual review passes for these states. The saved videos have not yet been reviewed for ripple/transition timing; TalkBack and physical haptics remain unverified. This is partial A-UI-01 evidence, not completion of PR-05b.

Fresh `pnpm check`, `pnpm test`, and `pnpm bundle` pass after the fixes (logs under `.artifacts/android/environment/controls-fixed-*.log`). The managed iOS regression passes all 14 native check groups, the normally signed simulator build and strict signature verification. English home passes in light/dark (125.03/118.36 seconds), and onboarding passes in light/dark (37.41/32.41 seconds). Results and recordings are under `.artifacts/android/ios-regression/controls-home/` and `controls-onboarding/`; the leased simulator is shut down on completion. Representative new-session sheet and onboarding button screenshots were reviewed in both appearances; this does not claim exhaustive visual or video review. Local artifacts have not been published to a remote acceptance service.
