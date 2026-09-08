# Offline UI verification

All UI baselines run without login, user data, cloud credentials, or a connected
machine. `EXPO_PUBLIC_UI_VERIFY=1` in a **development** bundle prevents account
restoration before Keychain/SQLite reads and disables login. The runner starts
its own Metro and requires the `ui-verify-ready` marker before any interaction.
Native image fixtures additionally require the `--ui-verify` launch argument and
compile only in Debug. No production credentials are used; the managed verification
Simulator is erased before each lease.

## Run locally

If a normal signed Debug app is already built, each verification command can lease
its own clean iPhone 17 Pro / iOS 26.5 device from the `Lody * Verify` pool:

```sh
pnpm verify:native
pnpm verify:ui --app /absolute/path/to/Lody.app
pnpm verify:ui --app /absolute/path/to/Lody.app --language zh-Hans --output .artifacts/ui-zh
```

For a verified build, wrap the build and checks so Xcode cannot select a personal
Simulator. The wrapper exposes its device as `LODY_VERIFY_UDID`; nested verify
commands use that lease automatically:

```sh
pnpm verify:simulator --name 'File Preview' -- zsh -euc '
  pnpm --filter @lody-ios/mobile native:assets
  xcodebuild -workspace apps/mobile/ios/Lody.xcworkspace -scheme Lody \
    -configuration Debug -sdk iphonesimulator \
    -destination "id=$LODY_VERIFY_UDID" \
    -derivedDataPath /tmp/lody-build build
  pnpm verify:native
  pnpm verify:ui --app /tmp/lody-build/Build/Products/Debug-iphonesimulator/Lody.app \
    --case file-preview --output .artifacts/file-preview
'
```

The allocator serializes selection and locks each leased device. It only considers
available, matching `Lody * Verify` devices; personal devices, other projects and
legacy runtimes are never candidates. Reserve that name pattern for disposable
verification devices. A shutdown candidate is erased, renamed to the current
verification, then booted. If none is free, one device is created.
Release shuts it down but keeps it for the next run. A device left booted after an
interrupted managed run can be reclaimed once its lock is gone; an untracked booted
device is treated as occupied.

`--udid` remains available for CI or an explicitly owned Simulator. Supplying it
bypasses leasing, erase, rename and shutdown, so its caller owns the full lifecycle.
Do not call `simctl create` directly for local verification.

Requires Python 3, AXe 1.8.0, Xcode 26.5 and the workspace dependencies.
`--case layout` selects one case (still both appearances). `--language` picks the
App Language the run launches with (`en` by default) and the catalog the scenes
assert against; run both before claiming bilingual coverage. `--port 8098` changes
the isolated Metro port; occupied ports are rejected. `--output PATH` selects an
artifact directory; use a new path for each run. The runner owns only its Metro
process group and app process. A small host-only CoreSimulator helper disconnects
hardware keyboard input for the leased device so keyboard geometry is actually
tested. No global Simulator preferences are changed. It never shuts down another
task's locked Simulator or Metro.

## Baseline inventory

`smooth-scroll` exercises cached history replacement, anchor preservation while
reading, streamed paragraphs/code, drag interruption and the production process
Sheet. It records video plus opt-in Debug-only UIKit geometry at display refresh
cadence (`--ui-verify-scroll`); the check requires intermediate scroll/height
frames in both hosts. Review the video for clipping and flashes before claiming
visual smoothness. The probe contains fixture IDs and geometry only.

| Case             | Production surface                                 | Behavior                                                                                                                                                                 |
| ---------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| settings         | RemoteSettingsView + RemoteSettingEditorScreen     | Leading Cancel/trailing Save while typing, compact Machine/MCP sheets, Agent prompt, failed load retry, failed-save Toast with draft retention, and saved-value readback |
| home             | NativeTabs + InboxScreen + creation Sheet          | 首页导航栏搜索、已归档结果、取消恢复；右下角新建反复打开并保留当前 Tab                                                                                                   |
| onboarding       | OnboardingScreen (non-dismissable pageSheet)       | No close button, swipe-down resists, connect → waiting code → cancel error → retry, sheet closes itself on sign-in                                                       |
| send             | NativeChat + shared send lifecycle                 | Offline immediate user/shiny rows, no pre-connection dispatch, failed text/attachment restoration, receipt reconciliation                                                |
| send-rounds      | NativeChat with retained history                   | Three accepted turns (short, wrapped, multiline), distinct IDs, cleared drafts, and native frame-by-frame landing checks                                                 |
| send-queue       | NativeChat + shared send lifecycle                 | Two sends while a reply runs, durable queue receipt unlocks composer, FIFO consumption, no duplicate draft                                                               |
| send-handoff     | NativeComposer sheet → NativeChat push             | Message UIView stays visible across navigation before creation; failed creation restores draft in target input                                                           |
| layout           | NativeChat + navigation title                      | Stream segments, completion folding, full conclusion, process-row height, send positioning                                                                               |
| tracking         | NativeChat                                         | User drag releases following, stable history, return button during/after streaming                                                                                       |
| model-memory     | CreateSessionScreen + ModelScreen + NativeComposer | Per-model effort and permission restoration across both selection hosts, full-access default                                                                             |
| model-options    | ChatComposerView                                   | Model/effort controls, RN echo, reopen persistence                                                                                                                       |
| image-preview    | ChatImageCell + ChatImagePreview                   | Synthetic bitmap, zoom/restore, button and gesture dismissal                                                                                                             |
| composer         | NativeComposer in a real form sheet                | Floating list inset, half/full sheet contrast, last-row reachability, file paste, keyboard clearance, rejection restore, duplicate suppression                           |
| composer-success | NativeChat composer                                | File paste, pending clear/lock, text and attachments stay cleared after acceptance                                                                                       |
| markdown         | MarkdownView code block                            | Copy preserves complete code and indentation through the Simulator clipboard                                                                                             |
| background       | DataRuntime + BGContinuedProcessingTask            | 同一 WebView 跨后台恢复、真实系统申请、完成/到期释放；系统拒绝时明确记录未验证长时执行                                                                                   |
| changes          | NativeChat + file diff page                        | Grouped file rows after completion, header totals, long paths, direct diff navigation, hidden warnings                                                                   |
| inbox            | NativeGroupedList + inboxSections                  | 动态分组；会话行是对话列表（标题前进行中圆点、时间在右、确认胶囊）；未读完成不进今天                                                                                     |
| composer-failure | NativeChat composer                                | Pasted-file, text and attachment restoration after rejection                                                                                                             |

Every case starts a fresh app process and navigates from Debug. Both light and
dark appearances run with default text size and English system controls. Product
copy is asserted through `catalog.text` / `catalog.plural`, which read the same
`apps/mobile/locales` catalog the app ships, so a scene proves the selected
language rather than a hardcoded sentence. Fixture content remains Chinese. Composer requests remain pending until the driver taps
Complete Request, so request timing cannot hide the busy state. These scenes
exercise production native draft contracts; they do not claim to cover cloud
persistence or Machine RPC. Those retain their existing behavior tests.

`verify:native` reuses chat, watchdog, local-store, status-label rendering,
composer, attachment and diff-font checks. The former ChatMarkdown-specific drawing and
block-selection tests referenced a deleted renderer and have been retired;
Markdown is rendered by the actual chat baseline, with screenshots/video for
review. There is no pixel-diff gate yet: screenshots are evidence, not automatic
proof of typography or animation quality.

## CI and future UI changes

`.github/workflows/verify.yml` runs Checks and Offline iOS UI on PRs and pushes to
main. Configure both as required checks in the repository branch rules before
relying on them to block merges. UI artifacts contain results.json, per-case
logs, screenshots, accessibility trees and video, including failures. Missing
scenes and timeouts fail the job. No login or distribution signing secret is used.

For each new UI behavior:

1. Add/reset a deterministic scene under development-only Debug. Reuse production
   views and the existing `present` contract; inject data or service outcomes at
   the owning boundary. Do not duplicate a production screen into a fake UI.
2. Add a runnable user-visible assertion and register it in the runner. New scenes
   must run independently on a freshly erased lease, without earlier cases or login.
3. Reproduce bugs with the original precondition; avoid internal constant-table
   snapshots. Prefer element-relative geometry and bounded state waits.
4. For shared UI, exercise each real host (e.g. chat and creation sheet). Add
   navigation/return integration cases when those boundaries change.
5. Review screenshots for appearance changes and video for keyboard/scroll/gesture
   changes. Baseline updates require review; never auto-approve a failed comparison.

Remote settings details now have an independent offline scene. It injects service
outcomes and checks the submitted values, but does not claim live cloud persistence.
Product catalog navigation and live cloud workflows still need separate acceptance.

后台用例通过 `--case background` 运行，模拟器 Home 停留 40 秒。计数来自真实离屏 WebView 回调；云端事件用本地脚本代替，不访问网络或凭据。若系统拒绝持续后台任务，该用例仅验证保留/恢复与申请失败降级，不能据此宣称后台长时执行已通过。长时间真机网络连接和能耗另需实测。

`--case home` 使用独立的 `EXPO_PUBLIC_UI_VERIFY_HOME=1` 开发包，在 Auth/Catalog Provider 边界注入内存数据，不启动认证或同步。完整运行会先以独立 Metro 运行该场景。新建只验证打开和取消；未绑定电脑的项目不读取电脑配置、不发送真实消息。

### 10,000-message performance demo

Settings → Debug → **10,000 条消息性能测试** loads 5,000 user messages and
5,000 Markdown answers through the production `NativeChat` collection. Tap the
play button to run a 20-second scroll at 8,000 pt/s (10 seconds away from the
current position, then back). Start at the bottom for the standard baseline.
The timed run visits part of the 10,000-entry dataset, not every message.

```sh
pnpm verify:ui --app <Debug.app> \
  --case chat-performance --output .artifacts/chat-performance --port 8103
```

The check repeats three times in each appearance. `performance-summary.json`
contains FPS, p95/max frame interval, over-budget intervals, visited section range,
and memory; `run-1.json` through `run-3.json` contain raw samples. Screenshots and
`run.mp4` capture the UI. Assertions verify the full dataset, both scroll directions,
more than 70,000 pt of travel, the measurement interval, and valid memory samples.
Performance values are reported without an arbitrary pass/fail threshold.

FPS measures `CADisplayLink` main-run-loop callback delivery, not GPU-presented
frames. Memory is the whole App process's `TASK_VM_INFO.phys_footprint` in MiB,
sampled every 250 ms; short spikes between samples can be missed. Baseline is
captured when play is pressed, after the dataset is loaded, not an empty-app
baseline. The sampler and video recording add overhead. Simulator Debug results
are regression baselines, not physical-device Release performance or proof of
absence of leaks. Native instrumentation is compiled only in Debug and stops
when its view leaves the window.

### Send animation frame checks

`send`, `send-handoff`, `send-rounds`, and `send-queue` enable the Debug-only `--ui-verify-throw` probe.
It requests the Simulator screen's maximum refresh rate and samples Core Animation
presentation geometry on every `CADisplayLink` callback, through 350ms after the
nominal flight. Each case saves raw `lody-throw-*.json` files and a
`throw-summary.json`: observed FPS, callback gaps, center-path deviation,
backwards movement, stationary interior frames, scale, and window-to-cell landing
error. Missing samples, a callback gap over 50ms, or a position discontinuity over
1.5pt fail the check. This measures main-thread callbacks and presentation-layer
state, not GPU-presented FPS; review the accompanying framebuffer video at its
original variable frame timestamps as well. Do not upsample the movie and call
interpolated or duplicated frames additional evidence.

`--case file-preview` exercises embedded Markdown file links in chat and the
process sheet, file-type symbols and VoiceOver actions, rendered Markdown/source
switching, document-relative links, and the shared file-browser preview. It also
opens PNG/PDF through system Quick Look and checks a missing-file error. The
Debug-only `ui-verify-files` reader supplies local fixtures before the cloud
runtime; this case does not claim live Machine RPC or every Quick Look format.

The throw probe also records each presentation frame's background color. It must
start at the rendered input surface color and interpolate toward the user bubble
color; both appearances fail if the color snaps directly to its destination.
Queue fixtures inject service outcomes only; protocol checks additionally verify
real Loro movable-list updates, persist-before-watermark ordering, and no replay
after an uncertain write. They do not claim a connected-machine cloud run.
