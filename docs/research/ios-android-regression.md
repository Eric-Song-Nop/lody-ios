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
