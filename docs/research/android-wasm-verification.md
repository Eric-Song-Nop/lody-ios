# PR-02 Android JS/WASM 验证记录

日期：2026-09-10。对应 [PR #3](https://github.com/Eric-Song-Nop/lody-ios/pull/3)，父 PR 为 [#2](https://github.com/Eric-Song-Nop/lody-ios/pull/2)。本记录证明离线数据宿主；阶段 B 的生命周期、持久化及真实账号接入尚未完成。

**构建与资产**

- 验证 commit：`78876e0eaba7af2f851519eab511cfdef87bf640`；WASM 和 bootstrap 两轮开始时工作树均干净。
- 内部 release APK SHA-256：`e553e62a151557b9c8d35e5e677077e23a0f41689e2398a8c7313128bf1d571a`。
- runtime HTML SHA-256：`0993a8efc917289e88da43d8cdcfb8b183ea60229f6e86298d6769e1138f901d`。
- 已直接读取 APK ZIP：runtime 与 iOS 生成资源逐字节相同，包内每份 fixture 的 SHA-256 与 manifest 一致。
- 本机 Apple M1；专用 AVD `Lody_Android_Verify_36`，Android 16 / API 36，arm64，host GPU，4096 MiB RAM。
- WebView provider：`com.google.android.webview`，`133.0.6943.137`。不能据此宣称所有 Android/WebView 版本兼容。

**模拟器结果**

| Case             | 实际结果                                                      | 对应计划     |
| ---------------- | ------------------------------------------------------------- | ------------ |
| increment        | 2 次完整目录投影与 Node 基线一致；真实 Loro history 导入成功  | A-WASM-01/02 |
| compressed       | 真实 Zstd 压缩 Flock 快照恢复，目录投影一致                   | A-WASM-01    |
| large            | 800 个会话的投影一致；266,349 UTF-16 码元跨多个桥接块完整交付 | A-WASM-04    |
| output-limit     | 输出超过桥接上限后原生宿主明确失败；没有目录投影或 live 成功  | A-WASM-03/04 |
| truncated-length | 截断长度头被拒绝，投影数 0                                    | A-WASM-03    |
| truncated-body   | 截断更新体被拒绝，投影数 0                                    | A-WASM-03    |
| invalid-json     | 无效 JSON 更新被拒绝，投影数 0                                | A-WASM-03    |
| over-limit       | 输入超过 8 MiB 被拒绝，投影数 0                               | A-WASM-03    |

全部场景 HTTP 写请求数为 0。large 场景记录 17 个桥接块（包括控制事件），峰值排队量 298,417 UTF-16 码元；这是一轮有界传输证据，不是长时间性能或实机内存结论。HTTP 响应由本地 fixture 提供，实际 StreamsClient、长度帧处理、WASM 与投影代码均未替换。

同一 APK 再次通过 A-BOOT-01/02：真实 Kotlin 常量正常，前后台计数 0 → 1，移除监听后仍为 1。截图确认内部页面状态栏可读、按钮和结果列表完整可见；24.18 秒 WASM 录像抽帧显示未运行→运行中→8 个场景通过，按钮在执行期间禁用。

**产物和复现**

本地产物在 `.artifacts/android/wasm-fenced/`：`result.json`、`runtime.json`、`wasm-passed.png/xml`、`wasm.mp4`、`video-review.png`、`logcat.txt` 和 `emulator.log`。bootstrap 回归在 `.artifacts/android/bootstrap-wasm-regression/`。目录被 Git 忽略，远端证据服务发布仍未完成，不能把此索引当成已上传视频。

```sh
pnpm build:android
pnpm verify:android --case wasm \
  --apk apps/mobile/android/app/build/outputs/apk/release/app-release.apk
pnpm verify:android --case bootstrap \
  --apk apps/mobile/android/app/build/outputs/apk/release/app-release.apk
```

工程检查：共享检查、112 个应用/原生 JS 测试、14 个模拟器工具测试、4 个 DOM WebView 测试及 iOS bundle 通过。Android 原生构建成功；最后一次修正后的增量构建耗时 36 秒。iOS 原生行为检查和签名构建正在专用模拟器上验证，尚不在本记录中声明通过。

**保留的失败与修复**

最初的字符串页面加载没有产生 ready 或 HTTP 请求，改用受控本地 HTTPS URL 直接提供资产流后真实链路通过。随后输出超限场景揭示：原生标记失败至异步销毁之间，已排队的旧事件仍可能被交付；现已在失败标记处立即屏蔽这些事件，并用同一失败场景重新验证通过。前序失败记录保留在 `.artifacts/android/wasm-first/`、`wasm-second/` 和 `wasm-final/`，不覆盖失败结果。

恢复、后台、账号隔离、Keystore/SQLite、真实 Cloud 授权和用户发送仍由后续 PR 交付；本轮不宣称它们可用。
