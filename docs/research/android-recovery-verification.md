# Android runtime recovery verification

Date: 2026-09-10. Roadmap PR-03, [draft #4](https://github.com/Eric-Song-Nop/lody-ios/pull/4), based on PR-02 / draft #3. This is an internal runtime capability, not the Android product entry.

## Implementation and ownership

`RuntimeSupervisor` owns one `RuntimeEndpoint` at a time. `RuntimeHealth` uses a monotonic clock with a 20-second startup deadline, an 8-second heartbeat deadline, and 1/2/4-second automatic retry delays. After the third automatic retry is consumed, further failure remains stopped in `failed` until an explicit start. Successful heartbeats do not silently replenish this budget.

Native Activity background/foreground callbacks suspend and resume the retained WebView; background time is excluded from failure detection. Generation fencing drops events and grant callbacks from replaced owners. Closing an endpoint settles pending bridge requests. The supervisor restores read subscriptions but has no write queue or replay path. A manual start resets the retry budget; stop releases the endpoint, timer and retained subscription list.

The verification entry is registered in the existing LodyKit module. The deterministic scenario uses real bundled WASM, offline HTTP responses, native callback withholding for startup/heartbeat faults, and actual `WebViewRenderProcess.terminate()` for renderer faults. The Python runner presses Home and returns to the Activity, exercising native lifecycle registration.

## Evidence rounds

| Round                       | Commit    | Evidence directory                   | Result                                                                         |
| --------------------------- | --------- | ------------------------------------ | ------------------------------------------------------------------------------ |
| First real recovery         | `0bdeedd` | `.artifacts/android/recovery-first/` | All five A-REC cases pass; screenshots and video contact sheet inspected       |
| Restored session assertions | `f8af9e6` | `.artifacts/android/recovery-reads/` | All five A-REC cases pass, including restored Loro content in four generations |

Final-round APK SHA-256: `9c554049f72ae81096d65fcae3de009d46551a460f7a399f14df1f852aa5ad7e`. Runtime report confirms read generations `[3, 4, 5, 7]`; all 5 created views are closed and HTTP writes remain zero.

First-round APK SHA-256: `75534785b464fc953fb307e2e547befc02a116415f318e47a26b52a140576ec1`.

Both builds use runtime SHA-256 `0993a8efc917289e88da43d8cdcfb8b183ea60229f6e86298d6769e1138f901d`, matching the PR-02 assets. The first round used the dedicated ARM64 Android 16 / API 36 emulator and WebView provider 133.0.6943.137. Five WebViews were created and five closed. The command log records one negative `sendTurn`, zero HTTP writes, and no replay after recovery. The video shows idle → running → background-ready → system Home → foreground → passed; the foreground event count changes from zero to one.

The stronger round also requires actual Loro session content after initial recovery, heartbeat recovery, renderer recovery and manual recovery. A `ready` callback alone does not satisfy these assertions. Final recovery screenshots/video were inspected. The same APK also passes all eight WASM cases in `.artifacts/android/wasm-recovery-regression/` and both bootstrap cases in `.artifacts/android/bootstrap-recovery-regression/`; these regression runs are recorded at documentation-only descendant `dd6dc89`.

## Supporting checks and limits

Android internal APK builds, `pnpm check`, `pnpm test`, and iOS `pnpm bundle` have passed during this PR. Build/check logs are under `.artifacts/android/environment/` with the `recovery` name. Prior normal-signing iOS native/build evidence is indexed in [the iOS regression report](ios-android-regression.md); PR-03 does not change iOS native source or bundled runtime code.

Parent CI run 34431969492 passed Android build and shared checks, then failed the offline iOS UI job. Its artifacts show the light case remained in the Expo developer launcher; the dark case reached the app but timed out reading the AXe tree. Logs and screenshots are retained under `.artifacts/android/ios-regression/ci-second-artifacts/`. CI is not green.

This report does not prove real Cloud account restoration, logout integration, foreground services, OEM background limits, physical device performance, or no duplicate writes after durable dispatch/ACK loss. Those remain PR-04, PR-09/10 and later stage responsibilities. Local evidence is retained; no remote acceptance publication is claimed. Stage B remains incomplete.

## Startup while suspended

Follow-up review found a duplicate 30-second startup timer in the low-level WebView endpoint. It could expire while the supervisor deliberately retained a background startup. Startup health now belongs only to `RuntimeSupervisor`; the standalone WASM verifier still owns its explicit per-case deadline. Recovery verification also suspends/resumes the owner while it is `starting` before exercising the startup timeout. Fresh emulator evidence for this follow-up is required; the earlier ready-state background result does not cover it.
