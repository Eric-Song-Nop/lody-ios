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

## Nested-return fix verified

Clean commit `38ad761` produced APK `ffba599dd85772e4408cc9857195c3288238d9e317e335ac90332191f2a9dffc`. `.artifacts/android/navigation-nested-back/` passes A-NAV-01/02 and the nested-return portion of A-NAV-03. The parent sheet remains visible with `Child result: cancelled`, and its Kotlin close control then settles the third outer cancellation. Screenshots and sampled video frames were reviewed. Visual inspection found internal route text in project-stack headers; `affcafa` wires that stack to the same presentation/title options and adds a separate `navigation-interruption` case for cancelled/committed edge gestures, immediate returns and preserved tab stacks. These additions need fresh evidence.

All 14 iOS native behavior groups, the normal-signing simulator build and strict signature verification passed for the shared navigation changes. The iOS UI run stopped before driving a scene because `axe` was missing from PATH; its attempted `navigation-licenses` output is not a UI pass. The managed simulator and Metro were cleaned up. The pinned AXe 1.8.0 tool from the existing CI workflow is being provisioned before retrying UI acceptance. The current iOS bundle also passes.

## Rapid return and evidence audit

Clean commit `93742f9`, APK `f7cdf28d050fd8c14ebcfb2a9d3335bffa2feb55315fc8fd869687ab51118cfb`, passed the `navigation-interruption-v1` runner on the API 36 ARM64 emulator. Artifacts are under `.artifacts/android/navigation-interruption-first/`. The committed edge swipe returns to Projects; three immediate return cycles settle in sequence; switching tabs retains the Sessions page. Reviewed screenshots also show the corrected `Sessions` header.

The v1 report labels its aggregate A-NAV-03 check as passing, but visual review of `back-gesture-preview.png` shows no active return preview. The attempted cancellation therefore proves page retention only, not interruption of an active predictive-back transition. Preserve the original report as produced; it is insufficient for full A-NAV-03 acceptance. Runner fixture v2 narrows the check to `A-NAV-03-rapid-return` and records cancellation/teardown gaps explicitly. Full PR-05a remains in verification.

AXe 1.8.0 is now installed with the CI-pinned archive checksum verified. The fresh managed iOS Simulator run completed successfully using the existing signed Debug app. `navigation-licenses-retry/results.json` records light/dark passes (57.08/48.99 s), and `navigation-home-retry/results.json` records light/dark passes (128.29/127.74 s), all with English app language. License list/detail screenshots, home video samples and the dark settings screenshot were reviewed. The runner exercises repeated sheet opening, inner navigation, search and return to the inbox; this is scoped UI regression, not the full iOS suite. The lease and isolated Metro were released. Artifacts remain local under `.artifacts/android/ios-regression/`; acceptance-service publication is pending because `lh` is unavailable.

## Continuous gestures and actual session release

`2ecdc63` adds internal-only observation of mounted pages, pending presentation results and actual IDs retained by the existing presentation store. Reset refuses live state. A sheet child can dismiss the whole Router host; both the outer result and the child result must cancel during teardown. These probes do not replace the production store or supply fake native APIs.

The test-only `GestureInput.java` now injects a continuous path with one down time through Android's input service. The former separate `input motionevent` commands each assigned a fresh down time, so they did not reliably represent one gesture. The driver is compiled to a DEX and run as the adb shell user; it is never bundled in the APK. Both the DEX hash and injection log are retained. The generated manifest currently has Expo's default `enableOnBackInvokedCallback=false`: the evidence establishes system edge-gesture recognition/cancellation, not a page-level predictive transition animation.

All rows below use the same internal release APK, SHA-256 `32bb7f3b01ebbc4659afd8baff6835e881876bba2aa13effeae5104de3c30021`, on the dedicated API 36 ARM64 emulator. Later commits in this table change runner checks or documents, not the application payload.

| Runner commit / fixture                  | Local artifacts                                        | Result and scope                                                                                                                                                                                                                                                               |
| ---------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `82a27ea` / `navigation-teardown-v1`     | `.artifacts/android/navigation-teardown-first/`        | Two host dismissals pass. Each shows mounted=0, pending=0, retained=0, observed=1, settled=2, cancelled=2.                                                                                                                                                                     |
| `277e885` / `navigation-v2`              | `.artifacts/android/navigation-sheet-paths-final/`     | Project/session/message traversal, system return, outer completion, system cancellation, Kotlin close, explicit cancellation, nested completion and downward sheet dismissal pass. Five outer results settle once.                                                             |
| `150e087` / `navigation-interruption-v4` | `.artifacts/android/navigation-gesture-cleanup-final/` | The held gesture visibly shows the system edge arrow; cancellation retains Sessions. A committed swipe, three immediate return cycles and tab-stack retention pass. Final teardown shows all five observed sessions released, all five results cancelled and no mounted pages. |

The preview and released-state screenshots, plus sampled navigation/gesture/teardown video frames, were reviewed. The continuous-gesture DEX hash is `f6174fc043bc8422d8760e2af0ba6f3ccbaea527a31b8070586054b0aee63979`. This resolves the earlier inability to prove an active **system edge gesture** before cancellation; it does not retroactively validate the v1 preview.

The new APK build, `pnpm check`, Python compilation and a fresh iOS production bundle pass. Shared iOS UI/native code has not changed since the signed build and four UI results above. The final toolbar-specific round is still pending: it separately exercises `Navigate up` on the inner sheet and on the sheet root. PR-05a remains in verification until that visible navigation path is accounted for. Full PR-05 still includes PR-05b's system controls, locale/theme and accessibility work.
