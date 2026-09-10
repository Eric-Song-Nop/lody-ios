# PR-01 Android bootstrap 验证记录

日期：2026-09-10。PR：<https://github.com/Eric-Song-Nop/lody-ios/pull/2>。此记录只证明内部 bootstrap；阶段 A 的 iOS 签名原生构建仍待完成。

**已验证的构建与设备**

- 构建 commit：`994bf911bfdf45aff09804317a86c2685edc8865`，验证开始时工作树干净。
- APK：`:app:assembleRelease`，内部验证入口，Expo 生成的开发签名；不是发行签名。
- APK SHA-256：`19bb902d9c1a9705304e7fba6902b29beceff4473c0831287326b81be57c0f01`。
- 本机：Apple M1；专用 AVD `Lody_Android_Verify_36`，Android 16 / API 36，`arm64-v8a`，host GPU，4096 MiB RAM。
- 系统 fingerprint：`google/sdk_gphone64_arm64/emu64a:16/BE2A.250530.026.D1/13818094:user/release-keys`。
- fixture：`bootstrap-v1`；SDK adb 使用独立 5038 端口。runner 结束后释放了自己启动的模拟器。

**行为结果**

| Case      | 结果 | 观察                                                                               |
| --------- | ---- | ---------------------------------------------------------------------------------- |
| A-BOOT-01 | 通过 | 冷启动进入内部验证页，真实 Kotlin 常量显示 Android 16 / API 36；浅色页面状态栏可读 |
| A-BOOT-02 | 通过 | 订阅时从后台返回，计数 0 → 1；移除监听后再次返回仍为 1，按钮切换为 Attach listener |

已审阅启动/移除监听截图及视频抽帧，状态转换与 UI hierarchy 断言一致。原始视频长 18.49 秒。无账号、Cloud、远端机器或凭据参与。

工程检查：`pnpm check`、已有应用/工具测试、双平台 bundle 和 prebuild 已通过；本次增量 Android release 构建成功，956 个任务中 68 个执行、888 个复用。

**本地产物与复现**

产物保留在工作区 `.artifacts/android/bootstrap-final/`：`result.json`、`boot.png/xml`、`detached.png/xml`、`bootstrap.mp4`、`video-review.png`、`logcat.txt`、`emulator.log`。构建日志为 `.artifacts/android/environment/build-final.log`。产物目录被 Git 忽略，此索引不代表远端评审者已经能下载视频；acceptance 服务发布尚未完成（当前环境无 `lh` CLI）。

```sh
pnpm build:android
pnpm verify:android --case bootstrap \
  --apk apps/mobile/android/app/build/outputs/apk/release/app-release.apk
```

**失败记录与尚未证明的项目**

初次较低内存 AVD 出现 System UI ANR，遮住应用并导致 case 失败，记录保留在 `.artifacts/android/bootstrap-first/`。提高专用模拟器内存、在原生构建完成后重试得到通过结果；这不能单独证明 ANR 的唯一根因。第一次通过截图发现状态栏对比度不足，修正后重新构建并得到上述最终证据。

iOS CocoaPods 安装完成，iOS 26.5 Simulator 官方运行时仍在下载；尚未执行完成签名 simulator build。WASM、聊天、存储、真机刷新率、推送和 OEM 后台行为均不在本次证明范围内。阶段 A 继续保持验证中。
