# Android system controls verification

Roadmap PR-05b is being implemented on `codex/android-05b-system-controls`, stacked on PR-05a (`codex/android-05a-navigation`, draft #6). This record describes the first control cohort, not completion of PR-05b or stage C.

## Implemented first cohort

- Kotlin `LodySymbolView`, `LodySymbolButton`, `LodyPressable` and `LodyGlassSurface` are registered through the existing LodyKit module. Symbol buttons use native click/long-click semantics, disabled state, ripple and 48 dp minimum bounds. The glass facade uses an ordinary opaque Android surface.
- NativeTabs now use licensed Material folder/settings resources for selected and unselected states. The current semantic mapping covers the internal scene only; unknown symbol names are rejected and product screens must add their actual mappings before entering the Android graph.
- Android `usePalette` resolves system text attributes and uses blue actions with neutral backgrounds. Android `AppText` uses the system font and native font scaling, without the iOS clamp or Menlo font name. The original iOS implementations remain the default files.
- The shared production `Button` is exercised through its actual native pressable/surface components in a regular page and a sheet. The wrapper enforces 48 dp Android minimums even when a caller requests the former 44 pt size.
- Material SVG sources, source URLs/hashes, an offline VectorDrawable converter and Apache-2.0 text are committed. Gradle includes the native license directory in the Android assets; the common license index includes Material Symbols.

## Behavioral cases

`pnpm verify:android --case controls --appearance light|dark --apk <internal.apk>` drives both hosts. It measures the native icon target against device density, checks click versus long-click counts, verifies disabled controls emit no actions, and taps the shared text button. It changes system appearance while each host is open and requires the existing count to survive, then returns to the requested appearance. The runner restores the original system night-mode setting during cleanup, including failed runs.

Each host emits an `A-UI-01-controls-*` subset result. Screenshots and video require review for icons, text contrast, ripple/surface layout and theme changes. These assertions do not establish TalkBack behavior or physical haptics.

## Current evidence and remaining work

`342d4bf` contains the first cohort; `b8fa5d3` adds native license packaging. `pnpm check` passes, including both TypeScript configurations, locale checks, generated licenses and formatting. Python compilation and local SVG conversion pass. Android build and emulator acceptance are in progress; no runtime pass is claimed yet.

PR-05b still requires native menus/context actions, grouped rows and their selection behavior, the remaining system APIs and semantic icons, generated Android strings/plurals, Chinese/English coverage, TalkBack and the final shared-host/iOS regressions. Those capabilities are not exported as placeholder native APIs.
