# Android 堆叠的 iOS 原生回归

日期：2026-09-10。本机原生行为检查及签名 Simulator app 构建均通过。

验证使用安装完成的 iOS 26.5（23F73）运行时和项目 lease 工具创建的 `Lody Android WASM regression Verify` 模拟器，UDID 为 `B6A92B61-8356-4338-B6CE-74BBDC6B5FD5`；流程结束后由 lease 释放。没有禁用签名，没有复制用户凭据。

iOS 输入来自 `7a79eb5` 堆叠中的源码与已生成资源。构建期间后续 PR-03 只修改 Kotlin 文件，没有修改 iOS 源码或资源。实际产物为 `/tmp/lody-android-ios-build/Build/Products/Debug-iphonesimulator/Lody.app`。

- `pnpm verify:native --udid "$LODY_VERIFY_UDID"` 完成全部 14 组原生行为检查，包括 chat-render、composer、watchdog、存储、附件、Diff 和系统列表控件。
- `chat-render` 编译耗时 17.4 秒，composer 编译耗时 8.6 秒；所有行为断言通过。
- `xcodebuild` 最终记录 `BUILD SUCCEEDED`，app 的 CodeSign 使用 `Sign to Run Locally`，保留正常 Simulator 签名流程。
- `codesign --verify --deep --strict` 对实际 app 返回成功。
- 实际 app 内 `DataRuntime.html` SHA-256 为 `0993a8efc917289e88da43d8cdcfb8b183ea60229f6e86298d6769e1138f901d`，与已验证的 Android APK 一致。

本地日志：`.artifacts/android/ios-regression/native-final.log`、`build-final.log` 和 `lease-final.log`。签名构建与原生断言不能替代完整 app UI 录像或真实 Cloud 联调，本轮不声明这些额外检查已通过。

远端之前的 iOS UI job 在 `chat-render` 的 Swift 编译达到 120 秒时超时，未进入该组行为断言。父 PR 的 `f8b61cf` 将编译预算独立为 300 秒，并记录实际耗时；行为执行仍为 120 秒，断言未删减。CI 复跑结果另行跟踪，不把本地通过写成远端通过。

## PR-04 storage regression

The managed `Android storage regression` lease completed all 14 native behavior groups and a normal-signing iOS simulator build on 2026-09-10. `codesign --verify --deep --strict` passed. Logs are `.artifacts/android/ios-regression/storage-native.log`, `storage-build.log` and `storage-lease.log`. The resulting app in `/tmp/lody-android-ios-build/Build/Products/Debug-iphonesimulator/Lody.app` contains runtime SHA-256 `0993a8efc917289e88da43d8cdcfb8b183ea60229f6e86298d6769e1138f901d`. The lease was released. This native/build check does not establish that the separately failing CI UI cases have passed.

## Parent PR-01 CI follow-up, 2026-09-11

[Run 34431969492](https://github.com/Eric-Song-Nop/lody-ios/actions/runs/34431969492) tests the PR-01 merge commit `ab05dbd` whose parents include `f8b61cf`. Checks and Android internal build passed; iOS UI failed after native build. Downloaded artifact `offline-ui-ab05dbd11b8aca6532398c389b436434841cceb7` records two distinct failures: light Home never reached `ui-verify-ready` and its reviewed screenshot shows the Expo development launcher; dark Home entered the real offline fixture but later `axe describe-ui` timed out after 20 seconds. Its screenshot shows the Home fixture, not the launcher. Neither result proves a product behavior regression or a successful CI run.

The failed iOS job has been requested for one unchanged-code rerun to distinguish a reproducible launch/driver failure from a transient CI failure. The rerun also failed: light Home timed out in AXe after 20 seconds; dark Home missed `ui-verify-ready`. Both rerun screenshots have now been reviewed and show the Expo development launcher, not the product fixture. The repeat run confirms an unresolved CI launch/driver problem; it does not establish a product regression. Rerun artifact ID is `10164484480`; Checks and Android build remain successful. No timeout, assertion or scenario was removed, and local Home passes do not substitute for this remote result.

## PR-05b TalkBack backdrop dependency patch

The managed `TalkBack backdrop iOS regression` lease completed a normally signed Debug simulator build and `codesign --verify --deep --strict` after generating native assets. Source is `d14ab0d` (including Android dependency patch `7841c7a`), with an accessibility report edit only. Logs are `.artifacts/android/ios-regression/talkback-backdrop-assets.log`, `talkback-backdrop-build.log` and `talkback-backdrop-lease.log`. The wrapper exits zero and releases the lease. The persistent react-native-screens patch changes Android's empty dimming view accessibility importance; no iOS source is patched. This build does not close the parent CI Home UI failure or claim a new iOS UI behavior run.
