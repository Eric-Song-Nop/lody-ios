# Android compiled language resources

PR-05b adds Android resources generated from the existing `apps/mobile/locales` JSON catalogs. The generator produces 101 native keys in default English and `values-b+zh+Hans`, collapsing `.one`/`.other` pairs into Android plurals. The iOS xcstrings generator remains in place.

Generation runs through both `native:assets` and the Android prebuild mod. `pnpm i18n:check` fails on stale resources. Kotlin resource IDs are generated explicitly, so resource shrinking does not depend on reflection. Native `LodyStrings` uses Android's quantity selection and then interpolates named parameters exactly once; argument contents remain literal. Missing keys, incorrect arguments and incorrect use of plural quantities fail explicitly. The close button uses the resource when the caller has not supplied an accessibility label and refreshes it on configuration changes.

Generator tests cover XML-sensitive characters, quotes, whitespace, backslashes, formatting-looking text, plural grouping, missing translations and normalized-name collisions. The device fixture reads every compiled resource using localized Android contexts for English, Simplified Chinese and Spanish fallback, including quantities 0/1/2. Its RN boundary compares each returned value with the shared source catalog and rejects missing or duplicate cases. It also checks four invalid native calls. This proves compiled resource lookup and interpolation, not a whole-app system-language switch or bilingual product acceptance.

Run `pnpm verify:android --case locales --appearance light --apk <internal.apk>`. The scene is offline and exposes only fixture text. Local screenshot/video/results remain under `.artifacts/android`; remote acceptance publication is separate. Android prebuild and the subsequent clean native build pass; `pnpm check`, `pnpm test` (including the generator cases) and `pnpm bundle` pass. Clean `a12007c` APK `57381b2a54604797d47ad83a99be804fab4280c54119b56f36ff718840fe0060` passes all 357 compiled-resource comparisons plus four invalid-input checks on the API 36 ARM64 emulator. Results are in `.artifacts/android/locales-oracle/`; the prior system appearance was restored and the owned emulator released. The rendered English, Chinese and fallback examples were visually reviewed. A fresh normally signed iOS simulator build and strict deep signature verification pass (`.artifacts/android/ios-regression/locales-build.log`); the managed simulator lease was released. The 14.01-second Android recording and half-second samples were reviewed alongside the full-resolution result screenshot. Broader system-font, TalkBack and product language coverage remain part of the unfinished PR-05 gate.

Reference: [Android string and quantity resources](https://developer.android.com/guide/topics/resources/string-resource).

The first `71fee44` device run stopped in the RN verifier because the installed Hermes does not provide `Intl.PluralRules`. `locales-first` preserves the failure. The verifier now uses explicit expected categories for its fixed en/es/zh quantities 0, 1 and 2; the production path still calls Android `getQuantityText`. No product polyfill was added.

## Runtime language synchronization groundwork

The Android entry now initializes the shared catalog before loading routes. A single root observer listens through Expo Localization's `useLocales` and re-reads `getLocales` on foreground; its AppState listener is removed on unmount. This follows the installed Expo 57 implementation and [Expo's Android lifecycle guidance](https://docs.expo.dev/versions/latest/sdk/localization/#behavior). The observer does not key or remount the Router, change presentation sessions, or clear drafts.

The shared translation store now notifies subscribers only when the supported language changes. `useTranslations` subscribes each consuming view through `useSyncExternalStore` and returns cached, language-bound translation functions. Existing imperative `t`/`tp` calls continue to read the current language; subscribing only at the root is deliberately insufficient for translated descendants. Node checks cover notifications, duplicate changes, listener removal, plural output and old render snapshots remaining internally consistent after a language change.

This is groundwork, not system-language-switch acceptance. Existing product components still need a call-site audit before Android product entry opens: translated labels, memoized collections/callback dependencies and module-time page titles must react coherently. The runtime case below exercises real application locale configuration changes, foreground return, page/sheet native labels, unsupported-language fallback and draft/navigation retention. Compiled-resource evidence above does not prove any of these runtime behaviors.

## Real application locale switching

`locale-switch` uses Android `cmd locale` to set and read the app's real locale override on API 36. It preserves and restores the original override. It does not call `setLocale` directly from a fixture. The scene contains an independently subscribed memoized translation component, a real editable draft, a native close button with its default Android resource label, and a retained click counter. Page and formSheet hosts use the production presentation contract. The shared SheetStack now subscribes its explicit close accessibility label to translation changes.

The first matrix used the release APK built from `cc0966f`, SHA-256 `393f62ab2b0d91d853c2fbeec383f7802b974513b4cbb01fec01c84879a55d9e`, with runner `05a604e`. The light page and sheet returned automated pass, but the return assertion was insufficient for the sheet: UI Automator also includes the destination beneath a dialog. On the dark page the same assumption failed outright: a single Back dismissed the IME restored on foreground instead of the page. Evidence remains in `.artifacts/android/locale-switch-first-*`; this matrix is not accepted as complete navigation evidence. The language state screenshots show the translated strings, native resource labels and retained draft, but do not repair the deficient return assertion.

Runner v2 (`2cdd442`) checks the system IME state, dismisses it when present, then separately dismisses the route and requires the language scene to disappear from the hierarchy. It also asserts the sheet header's translated accessibility label. The four-case rerun uses the identical APK; results are below. This case does not cover global device language settings, every product call site, TalkBack speech/focus, process death or keyboard composition.

The v2 matrix completed on API 36 ARM64 and restored both the app locale override and system appearance in every case. All four behavioral cases passed. Each of the 20 locale/dismissal screenshots was opened individually, and 5-second video samples spanning every complete recording were reviewed. **The dark cases failed visual review**: after the background locale change, status bar icons become dark against the dark background until leaving the route. Runtime-language acceptance remains incomplete pending this fix and rerun.

| Evidence directory under `.artifacts/android/` | Behavior | Visual                              | Video duration |
| ---------------------------------------------- | -------- | ----------------------------------- | -------------- |
| `locale-switch-return-page-light`              | pass     | pass within fixture scope           | 79.440278 s    |
| `locale-switch-return-sheet-light`             | pass     | pass within fixture scope           | 81.909344 s    |
| `locale-switch-return-page-dark`               | pass     | failed: status bar after foreground | 71.356478 s    |
| `locale-switch-return-sheet-dark`              | pass     | failed: status bar after foreground | 77.256011 s    |

All use runner `2cdd442` and the same `393f62ab…` APK above. The first starts with a clean working tree; the remaining three record uncommitted documentation-only changes. Their production source and runner are unchanged. The emulator was shut down by its owner after the matrix. Local `visual-review.json` files preserve the separate visual decisions; automated `result.json` pass is not full acceptance. The new shared SheetStack subscription also still requires the corresponding iOS UI regression. PR-05b remains incomplete, and remote acceptance publication is unavailable because `lh` is not installed.

### Foreground status-bar ownership repair

The runtime probe remained mounted beneath the navigation verification route. Its real app-active subscription increments a counter on foreground, re-rendering a fixed `StatusBar barStyle="dark-content"`. In the installed React Native implementation, `StatusBar.componentDidUpdate` replaces the global stack entry and Android `_updatePropsStack` writes the merged style even when the prop value is unchanged. That overwrote the visible Native Stack's light icons. This explains the foreground-only failure and why leaving the route restored contrast.

`3d2a0ea` removes that redundant StatusBar component from the runtime probe. The root Stack's existing `index` option still explicitly requests dark icons for the white probe page; visible navigation screens retain their theme-dependent native Stack configuration. No Activity callback, delayed recoloring or new native bridge was added. Runner v3 (`eb6199e`) reads WindowManager's status-bar appearance regions at each locale checkpoint and fails on theme-inappropriate icon appearance, in addition to the screenshots. New release build and `pnpm check` pass. The new four-case matrix completed; the v2 visual failures above remain historical evidence. Results and scope follow.

### Status-bar repair verification (v3)

All four API 36 ARM64 cases passed on release APK SHA-256 `6ee499dd2578264d683f7f7740dfd54fa47e5871d95f60e9bbf6ac942f2c16c3`, built from production change `3d2a0ea`. Runner v3 adds four actual WindowManager appearance-region checks per case. All 24 screenshots (boot, four language states and dismissal per case) were individually opened; 5-second samples spanning each complete video were reviewed. Dark icons remain on the white runtime probe, and light icons remain on dark native navigation through background/foreground and language changes. Draft/counter/process retention and actual route removal passed. Both app locales and system appearance were restored.

| Directory under `.artifacts/android/` | Runner checkout                                | Video duration | Behavior and scoped visual review |
| ------------------------------------- | ---------------------------------------------- | -------------- | --------------------------------- |
| `locale-switch-statusbar-page-light`  | `eb6199e`, clean                               | 74.643633 s    | pass                              |
| `locale-switch-statusbar-sheet-light` | `eb6199e`, documentation-only dirty tree       | 85.173589 s    | pass                              |
| `locale-switch-statusbar-page-dark`   | `0f6b266`, clean; documentation-only successor | 75.955789 s    | pass                              |
| `locale-switch-statusbar-sheet-dark`  | `0f6b266`, clean; documentation-only successor | 84.456944 s    | pass                              |

The matrix owner shut down the Android emulator, then sequentially ran iOS Home using the existing normally signed Debug native app and fresh isolated Metro on port 8107. Both English Home behavior runs passed (light 126.30 s, dark 121.43 s), under `.artifacts/android/ios-regression/locale-sheet-home`. The compact/full New Session sheet and cancellation-return screenshots were individually reviewed in both themes: title, close control, native composer and return remain visible and correctly positioned. This is scoped shared-SheetStack regression evidence, not a claim that every Home screenshot or complete video was visually reviewed. No iOS native code changed in the language subscription/status-bar repair.

The process completed with exit code 0. Local visual decisions are saved separately from automated results. This accepts the foreground status-bar repair and the tested language fixture only. Module-time page titles, cached product translation call sites, system fonts and TalkBack remain PR-05b work; product entry remains closed. Remote acceptance publication remains unavailable (`lh` is absent).

### Reactive page titles (v4 verification)

`7bc592a` changes the existing presentation title contract to accept either literal text or a translator callback. The callback receives the current render's translator; literal user/server titles remain unchanged. Twenty-six module-time page-title translations now resolve at render time. SheetStack resolves both root and pushed-level headers, and its default close label uses the actual presentation override when present. Presented push routes subscribe and update the native Stack title without changing route/session identity.

The existing language fixture now uses a translated title. Runner `locale-switch-v4` requires the native title and sheet close label to change together through the real application locale sequence, while preserving the existing draft, process, return and status-bar assertions. `pnpm check`, `pnpm test`, iOS bundle, Android bundle and Python compilation pass. The new release build and four-case Android matrix passed; v3 evidence alone does not prove this title change. Detailed v4 provenance follows below.

Call-site findings recorded before the migration (follow-up status below):

| Source                                                                            | Finding                                                                                                      | Required follow-through                                                                                                                                                 |
| --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/screens/InboxScreen.tsx`                                                     | `sections` memo depends on mode/catalog/accent/expansion, not locale; row helpers translate labels and dates | Subscribe at the view and invalidate derived sections on locale changes; preserve query, expansion and scroll position                                                  |
| `SettingsScreen`, `RemoteSettingsScreen`, `CreateSessionScreen`, settings preview | Some presentation overrides eagerly call `settingsTitle` or `t`                                              | Pass render-time title callbacks; verify an already-open override and a pushed level, preserving the edited draft                                                       |
| Product views importing imperative `t`                                            | Parent rerenders are not a per-view subscription guarantee; memoized children can retain copy                | Move rendered copy to `useTranslations`, include translator in derived-data dependencies, and cover each exposed host                                                   |
| `src/ui/time.ts`, session row/status helpers, transcript aggregation              | Derived display strings depend on current locale                                                             | Separate render projections from persisted user/server text; invalidate translated projections without resubscribing or rebuilding the data replica                     |
| Cloud failures, toast/action callbacks                                            | Event-time copy and historical error text differ from continuously rendered labels                           | Keep imperative translation for newly emitted messages; translate structured product failure states at display time where appropriate; never translate user transcripts |

These findings do not permit opening Android product routes before their roadmap dependencies. Font/TalkBack and remaining system-control work are still tracked separately in PR-05b.

### Title matrix results and shared call-site follow-up

The four `locale-switch-title-{page,sheet}-{light,dark}` cases use release APK SHA-256 `7eda271e922948bdf4e8b4672d26d8b78373267772703cb11ebe7f696b8c089d`, built from `7bc592a`, on API 36 ARM64. All pass the v4 assertions. Each case has six individually reviewed screenshots and a complete recording reviewed at 5-second intervals; local `visual-review.json` records this scoped review. The translated Settings/设置 title, close label, draft and counter remain correct; dark status icons retain contrast after foreground return. Locale override and appearance restoration passed.

| Case        | Runner checkout                                | Video duration |
| ----------- | ---------------------------------------------- | -------------- |
| page light  | `40be78f`, clean                               | 68.786300 s    |
| sheet light | `40be78f`, product call-site edits in progress | 81.261589 s    |
| page dark   | `ffffd1e`, clean                               | 68.532611 s    |
| sheet dark  | `ffffd1e`, clean                               | 72.603311 s    |

Runner checkout changes did not change the installed APK. In particular, these cases do not verify the later product call-site migration. Sequential iOS Home passed in light (127.55 s) and dark (122.20 s), under `.artifacts/android/ios-regression/locale-title-home`. It used the existing normally signed native Debug app with fresh Metro; environment provenance records `ffffd1e` plus uncommitted projection-hook changes later committed in `5a0c046`. Six New Session compact/full/cancelled screenshots were reviewed: headers, close controls, composer and return layout remain readable and correctly positioned. This is scoped shared UI regression, not full Home visual/video acceptance or an iOS system-language-switch test.

`ffffd1e` subscribes rendered product copy and updates memo/callback dependencies and presentation overrides. `5a0c046` extracts the actual Inbox projection memo into `useInboxSections`, invalidating it on supported locale changes while preserving catalog identity. The Android offline scene consumes that same hook with constant catalog inputs inside a memoized component. Runner v5 additionally requires translated section/badge copy and unchanged user-authored title at every language checkpoint. Shared projection type aliases are type-only; they do not widen the Android native list's supported props or enable unimplemented fields.

The projection change passed `pnpm check`. Its new APK and v5 matrix are under verification; v4 is not evidence for it. Full product-host coverage, event-time failure copy, font behavior, TalkBack and remaining list behavior still prevent declaring PR-05b complete. Android product entry remains closed.

### Projection v5 failure: compiler removed locale invalidation

The first projection matrix stopped on page/light at the Chinese checkpoint. APK SHA-256 `564d4f745620822045c6de2f8072516cd8a9b5f03bba30bf19cb6554e54fecb6` was built from `5a0c046`; evidence is retained in `.artifacts/android/locale-switch-projection-page-light`. English projected copy passed, but the Chinese projection assertion failed. The matrix exited 1, shut down its owned emulator, and did not reach the remaining three cases or the sequential iOS run. The generic failure screenshot was captured after locale cleanup and therefore shows restored English; it cannot establish the original failure state. The recording contains the Chinese interval. The runner now records failed-checkpoint text and captures before restoration when this assertion fails.

The installed React Compiler transform of `useInboxSections` explains the stale projection: it generated cache conditions for accent/catalog/expanded/mode and omitted locale entirely. The projection helpers read the imperative translation store, which is not a visible call argument. `e9f5e18` adds a function-local `use no memo` directive so the existing explicit `useMemo` locale dependency survives; compiler configuration elsewhere is unchanged. A transform inspection confirms the manual locale dependency is retained. `pnpm check` passes. A new release build and identical v5 matrix are running in fresh `locale-switch-compiler-*` directories. This is an implemented repair awaiting device proof, not a passed projection result.

### Compiler follow-up audit and first repaired device result

Release build `e9f5e18` passes in 5m05s; APK SHA-256 is `57d3e05169e95dee5c291d045e18c60720a0de4f57030d1a08a40344fa06b7d7`. The first repaired v5 case, `locale-switch-compiler-page-light`, passes with clean runner checkout `82f68bb`. Its four language-state and dismissal screenshots were reviewed: projected category/badge switch to Chinese, user title remains literal, and draft/counter survive. Boot screenshot/video review and the remaining matrix are not yet complete, so full repair acceptance remains pending.

The follow-up compiler audit found the same hidden dependency in Archived Sessions rows and License sections. Project rows already include the bound translator in their compiled cache dependency; the inspected Inbox view did not hoist its search call. `933fe7e` passes the render translator into archived row badge/action/menu projections and license headers/footers. The installed compiler now includes that translator in both caches. The archived-row behavior test checks English/Chinese badges and all action labels while preserving the user title. `pnpm check` and the targeted Inbox test pass. These later source changes are not present in the current Android APK; the sequential iOS Metro run will consume the current source and must record its own provenance.

### Completed compiler-repair matrix (v5)

All four `locale-switch-compiler-{page,sheet}-{light,dark}` cases pass on the same API 36 ARM64 release APK built from `e9f5e18`, SHA-256 `57d3e05169e95dee5c291d045e18c60720a0de4f57030d1a08a40344fa06b7d7`. All 24 screenshots were individually reviewed, together with 5-second samples spanning all four recordings. Each case checks the real en → zh → unsupported-language fallback/background return → en sequence, production Inbox projection copy, unchanged user title, retained draft/counter/process, native title/close label, status-bar appearance and actual dismissal. Original empty app locales and system night mode `no` were restored.

| Case        | Runner checkout (clean) | Video duration | Behavior / scoped visual review |
| ----------- | ----------------------- | -------------- | ------------------------------- |
| page light  | `82f68bb`               | 80.423111 s    | pass                            |
| sheet light | `933fe7e`               | 81.425700 s    | pass                            |
| page dark   | `3005a2e`               | 79.798111 s    | pass                            |
| sheet dark  | `3005a2e`               | 81.966289 s    | pass                            |

Runner checkout changes do not change the installed APK: this proves the Inbox compiler repair, not the later Archived Sessions/License product-host changes. The original failed projection run remains preserved above.

After Android owner cleanup, sequential iOS Home passed in light (125.91 s) and dark (122.07 s), under `ios-regression/locale-compiler-home`. It used the existing normally signed native Debug app with fresh isolated Metro. Provenance records `3005a2e` and a dirty tree containing verification work; the source includes `933fe7e`. Six compact/full/cancelled New Session screenshots were individually reviewed and recorded in `visual-review.json`: title, close control, native composer and return layout remain readable and correctly positioned. This is scoped shared UI regression, not complete Home visual/video acceptance or device-language verification of Archived Sessions/License screens.

This closes the tested v5 Inbox projection repair. Remaining product-host coverage, list edge behavior, system fonts and real TalkBack checks still prevent declaring PR-05b complete. Android product entry remains closed.
