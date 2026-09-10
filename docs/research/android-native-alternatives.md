# Lody Android 原生组件替代研究

Android 生态已经有比“RecyclerView 加通用 Markdown 库”更贴近 Lody 的方案。其中，Enriched Markdown 的 React Native Android 实现最值得作为原生富文本引擎候选，mikepenz 的 StreamingMarkdownState 最值得作为增量解析候选，RaTeX 是数学排版的重点候选，JavaScriptSandbox 则可能比离屏 WebView 更适合纯计算数据引擎。它们分别在不同层面有优势，目前没有证据表明某一个现成项目能整体超过或完整替换 Lody 的 Swift 组合。

选型应保留现有优化的行为契约：稳定内容不重复排版、显示进度与服务端状态分离、系统文本选择、移动端复杂内容排版、有限恢复、凭据隔离和可靠草稿交接。技术栈名称、功能清单、星数或演示动画都不能单独证明这些契约成立。

**1. 研究范围与证据边界**

本文覆盖 README 的原生导航、聊天虚拟化、Markdown、字形渐入、输入框、Diff、文件预览、离屏 WASM、恢复与后台执行、SQLite、认证与安全；补充当前仓库已有的推送、图标、国际化和验证工具。目标是保留 iOS 质量并为 Android 挑选合适组件，不涉及改写云协议或切换后端。

资料核验截至 2026-09-09。本地基线为 `cc5c1a16b55b6cb51882b7e6a9c67a55f2346fd1`。上游源码固定 revision、发布渠道元数据和 npm 包校验值记录于 [证据清单](android-native-alternatives-evidence.json)。本文区分三类结论：源码或官方文档可确认的事实、基于事实作出的选型判断、尚待真机验证的行为。

没有运行 Android 原型、设备性能测试或截图对比，因此不提供推测的 FPS、内存、启动耗时、维护工期，也不把上游自述的性能收益当作 Lody 的实测收益。源码测试被阅读用于确认设计意图；没有把“存在测试”写成“本地测试通过”。

**2. Swift 基线真正值得保留的设计**

本地插件固定 MarkdownView `4.3.2`、Litext `2.2.2`。MarkdownView 本身明确优先考虑手机排版与流式展示，并不追求完整 CommonMark；例如把列表中的复杂表格和代码块提升为独立块。Litext 提供 CoreText 排版、文本选择、原生视图附件和绘制扩展点。Android 候选即使更符合 CommonMark，也不自动意味着更适合手机阅读。[^1][^2]

Lody 在这些库之上还有大量关键逻辑。下表依据当前源码，而不是早期设计文档；旧文档中的节流和组件结构已有演进。

| 行为           | 当前实现                                                                  | Android 必须保留的性质                        |
| -------------- | ------------------------------------------------------------------------- | --------------------------------------------- |
| 解析与显示分离 | `ChatParseCache` 缓存解析结果；流式块比较后复用                           | 解析可在后台，旧任务不得覆盖新结果            |
| 稳定段落复用   | `ChatMarkdownStore` 为未变化块保留对象，`ChatMarkdownView` 保留视图和排版 | 新 token 不应使全部已完成段落重新安装文本     |
| 测量与显示一致 | 同一原生视图用于测量和显示，另有高度缓存和有界离屏视图池                  | 列表预估高度与真实展示不能持续互相纠正        |
| 字素渐入       | `ChatTextFade` 比较渲染后的字素，保留旧文字的出生时间                     | Markdown 标记闭合、修正文案时旧文字不重新闪烁 |
| 绘制与布局分离 | `ChatFadeLabelView` 的动画 tick 只请求重绘；CoreText run 分段设置 alpha   | 动画不能在每帧重新解析或排版全文              |
| 流式负载调节   | 短尾部逐步显示；超过 1024 UTF-16 长度或积压达到 48 字素时采用更大批次     | 突发输出不能变成持续数秒的动画积压            |
| 完成态选择     | 流式时按块复用，完成后合并为一个原生正文选择范围                          | 跨段落选择与复制不能因为优化被永久拆碎        |
| 滚动跟随       | `ChatScroll` 使用时间收敛，考虑像素舍入                                   | 刷新率不同仍应连续；用户上翻时不夺回滚动      |

上述性质应转成共同验收场景，具体的缓存大小、阈值和动画时长不必在 Android 原样照抄。尤其 README 的 60/120 fps 描述不能充当新平台的性能证据。[^3]

**3. 组件候选总表**

表中“优先”表示值得进入验证，并非已经决定采用。详细依据见后文。

| 原能力                  | Android 优先候选                                    | 次选或参考                                  | 当前判断                                      |
| ----------------------- | --------------------------------------------------- | ------------------------------------------- | --------------------------------------------- |
| FlowDown 式精细聊天体验 | Lody 自有行为层 + 原生渲染引擎                      | RikkaHub、官方 Compose 示例                 | 没有找到可直接替换的整套底座                  |
| MarkdownView + Litext   | Enriched Markdown 的 RN Android 引擎                | mikepenz renderer；独立 Kotlin SDK；Markwon | RN 引擎能力最贴近，独立 SDK 尚未等价          |
| 增量 Markdown 解析      | JetBrains streaming parser，经 mikepenz 集成        | md4c 全量解析 + 原生块复用                  | 增量解析有优势，但必须处理文本修正            |
| 字形/尾部渐入           | Enriched 的 FadeInSpan + 原生调度                   | Compose 自定义绘制                          | 已有可复用机制，仍需补字素和修正语义          |
| LaTeX                   | RaTeX Android                                       | AndroidMath；JLaTeXMath Android             | RaTeX 优先比较，不能以语法覆盖率代替排版验收  |
| 语法高亮                | tree-sitter；SnipMe Highlights                      | Prism4j；RikkaHub highlight 模块            | 按代码块和完整文件两个场景分别选              |
| 虚拟聊天列表            | RecyclerView 或 Compose LazyColumn                  | FlashList v2                                | 由最终渲染边界决定，不能提前宣布某个必胜      |
| 原生输入与键盘联动      | EditText + Insets，或 state-based Compose TextField | react-native-keyboard-controller            | 草稿和附件事务仍归 LodyKit                    |
| 全屏 Diff               | 保留 Pierre + Android WebView 宿主                  | 原生 Diff 视图 + java-diff-utils            | 尚无足够证据支持替换 Pierre                   |
| 完整代码文件            | Sora Editor 只读模式                                | 高亮文本 + 行号；现有网页文件视图           | Sora 在编辑器能力上更强，是否过重需测         |
| 文件树                  | 原生列表 + 现有远端目录模型                         | 无须专用本地文件管理器库                    | 目录数据语义比树形控件更重要                  |
| Quick Look              | Coil 图片、AndroidX PDF、系统文件打开               | 按文件类型增加专门预览器                    | 无完全等价的统一入口                          |
| 离屏 JS/WASM            | WebView 与 JavaScriptSandbox 对照                   | 原生 Loro FFI；自带 JS/WASM 引擎            | WebView 兼容优先，Sandbox 结构更贴合纯计算    |
| SQLite 投影             | Android SQLite；需要类型约束时用 Room               | SQLDelight                                  | 保留单一投影 owner；不引入第二个 live replica |
| Keychain                | Android Keystore + 私有加密凭据存储                 | 已有安全存储 facade                         | 不能直接把 token 当 Keystore 密钥             |
| 导航与分组行            | Expo NativeTabs / Stack + Material 组件             | Compose 局部宿主                            | 保留 `present()` 结果语义，适配系统返回       |
| Push                    | OneSignal Android                                   | 根据目标设备补 HMS 等通道                   | 保留冷启动点击缓存与账号 fencing              |
| 原生验收                | UI Automator + Macrobenchmark / Perfetto            | Compose UI tests、Espresso                  | 图片、视频、行为断言和性能数据各司其职        |

**4. Enriched Markdown：当前最贴近的富文本候选**

Software Mansion 的项目已扩展为 `enriched-markdown` 多包仓库。核验到 RN npm 稳定版本为 `1.0.2`，独立 Android Maven 包为 `0.1.0`。官方兼容表明确区分两者：RN 已支持 GFM、公式和流式展示，独立 Kotlin 入口仍将这些能力列为待支持。不能从仓库首页的综合功能清单推导所有包都有相同能力。[^4][^5]

为了避免把主分支功能误写成已发布功能，另行检查了 npm `1.0.2` 发布包里的 Kotlin 源码。它已有 `SegmentReconciler`、尾部渐入和表格新行动画；但代码组织、依赖版本与主分支不同。发布包依赖 RaTeX Android `0.1.10`，本次检出的主分支依赖 `0.1.14`。升级评估必须分别验证这两个版本，不应把主分支修复默认计入稳定包。[^6]

**与 Lody 特别接近的机制。** 发布包的分块对齐先找同位置同签名的原生视图，再按内容签名寻找可复用视图，最后更新同类型视图或新建。这比简单地每次替换整棵 Markdown 视图树更贴近 Lody 的稳定块策略。表格、公式、代码和正文由不同的原生视图承担；代码围栏未闭合和表格未完整的状态另有流式处理。[^7]

**渐入并非从零实现。** `TailFadeInAnimator` 用 Android `CharacterStyle` 修改新增范围的绘制颜色 alpha，再由 `ValueAnimator` 驱动重绘，支持系统减少动画设置。它没有每帧重新调用 Markdown parser。但其新增区间按旧、新文本长度计算，使用一次追加范围的 150 ms 渐入，不等价于 Lody 对渲染字素逐个保留时间、处理任意修正的逻辑。[^8]

**仍然需要审查的差距。** GFM 路径仍会对提供的 Markdown 进行解析和分段渲染，再复用稳定视图；“视图复用”不能写成“解析已经增量化”。发布实现为容器创建单线程 executor，过期结果在交付时由 renderId 拦截；若上层每个 token 都提交任务，仍应验证过时任务是否造成 CPU 和队列浪费。虚拟化列表复用时，取消、清理和重新绑定也必须验证。[^7][^9]

选择能力需要按层次测试：正文单 TextView 的系统选择、跨普通段落、跨代码/表格的选择、复制 Markdown、以及动画期间拖动手柄。独立块具有自己的原生交互，不表示整个消息自动拥有统一选择范围。Lody 当前完成态合并正文的做法，是候选比较中的独立要求。

**接入方式决定成本。** 直接使用 RN 组件最容易获得目前完整能力，但它不能直接塞进 Kotlin RecyclerView 单元格，当作一个无 RN 依赖的普通 View。若坚持聊天整个原生宿主，就要考察独立 SDK 扩展，或将成熟 RN Android 引擎中的平台层与 Fabric 测量、事件依赖分离。后者意味着明确的维护工作，不能以“已有 Kotlin 代码”当作零成本复用。

推荐把它排在验证第一位：先证明已发布 Android 引擎的行为，再选择 RN 行宿主还是 LodyKit 原生宿主。若需要上游扩展点，优先提交小范围改动；当前 iOS 也采用了给 MarkdownView/Litext 补注入点、把专有动画留在 LodyKit 的方式。[^3]

**5. mikepenz renderer：更有潜力的增量解析路线**

Maven Central 元数据已确认 `multiplatform-markdown-renderer` `0.45.0` 发布；检索缓存中的 GitHub `latest` 一度指向 `0.43.0`，因此此处以发布仓库为准。`StreamingMarkdownState` 从 `0.42.0` 的迁移说明开始出现，使用 JetBrains Markdown 的 `StreamingMarkdownFile`。[^10]

它把输出分为 `stableAst` 和 `unstableAstTail`，追加内容时保留稳定 AST，继续解析尾部。读取的测试明确覆盖稳定节点身份保留、空追加不重复发射状态、稳定/尾部引用定义收集。这是比“每次全文解析，只把稳定视图保留下来”更深入的优化，有可能减少长回复反复解析的成本；实际收益仍取决于文本结构和尾部大小。[^11][^12]

**这条路线尤其值得保留为挑战者。** Lody 当前 parser 仍是完整文档解析，原因之一是稍后出现的引用和公式可能影响前文。Android 若选择增量 parser，必须验证同样的语义，而不是只比较追加普通段落的 benchmark。

API 的明确边界是只追加：`append(chunk)` 收到的是增量片段，不是每次完整消息。Lody 接收的内容可能有服务端修正、回退、重连替换，也可能只是相同长度的新文本。适配层必须先识别前缀追加；不是追加时重新构建解析状态，并保证旧状态结果不再进入视图。官方 Flow 示例直接 collect 后 append，不能假设 `suspend` 会自动把解析移出主线程。[^11]

这也是 Compose 渲染库，而非独立 Android TextView 引擎。Material 主题、Coil 和高亮扩展较方便，但此次没有找到足够证据证明它原生提供了 Lody 所需的字素渐入和同等完整公式交互。公式与动画都应单独验证，不应在总表中标为默认具备。[^10]

Compose 的选择机制也要正确使用。官方文档说明，把 LazyColumn 放在 SelectionContainer 内，对尚未 compose 的文本执行全选/复制具有不完整行为；已经选中的项会被保留，但尚未创建的项不会凭空进入选择。这不意味着 Compose 无法做聊天选择，而是不能依靠在整个虚拟列表外面套一个选择容器解决全文选择。[^13]

推荐让它与 Enriched 进入同一套内容基线。如果它在长流式回复明显减少解析成本、同时可补齐公式和选择体验，Compose 聊天宿主就有充分理由成为正式方案。不要先因 UIKit 对应关系锁死 RecyclerView。

**6. Markwon、其他富文本库和整应用参考**

Markwon 仍有明确价值：成熟的 TextView/Spannable 路径，表格、JLaTeXMath、Prism4j 等扩展，能够方便地嵌进传统原生列表。问题是本次取得的默认分支最新 commit 日期为 2021-03-15，GitHub 最新 release 指向 `4.6.2`；这些维护信号与本项目要持续优化 LLM 流式交互的需求不匹配。不能据此断言它所有分支无人维护，但不宜再将它直接列为首选。[^14]

compose-richtext 将 AST、富文本和 Compose 展示分层，适合想自行控制整套排版的团队；Compose Rich Editor 更侧重可编辑富文本、HTML/Markdown 转换。两者都值得按具体缺口选用，但本次没有获得其可直接覆盖 Lody 流式契约的证据，不能仅因“原生富文本”就替代当前组合。[^15]

RikkaHub 是最值得阅读的 Android 整应用参考之一：Kotlin/Compose、复杂 Markdown、公式、工具调用和文件内容都与 Lody 接近。源码显示它使用定制 JetBrains Markdown 与 JLaTeXMath 分支，后台 `mapLatest` 解析、定制代码高亮和不同富文本展示路径，体现了真实产品中的针对性工作。它应被当作产品行为和实现经验来源，而不是一个可以安装的聊天底座。[^16]

一处关键差异尤其重要：本次固定 revision 的 `ChatMessage.kt` 在流式生成时不套 SelectionContainer，完成后才开启；源码注释说明这是为避开文本反复注册与选择工具栏交互的问题。该事实不能推广为所有 Compose 版本的必然限制，但足以说明 RikkaHub 当前行为并非 Lody 流式选择要求的现成答案。[^17]

FlowDown 是现有 Apple 渲染组合的产品来源。没有找到一个经过等价验证的 Android “FlowDown 全套移植”。GetStream/CometChat 的完整聊天 SDK 则有自己的服务与数据模型；Lody 已有云端 Streams、Machine RPC 和副本 owner，引入整套 SDK 会制造额外边界。可阅读其控件实现，不建议以其客户端替换 Lody 数据层。[^18]

**7. 数学公式和代码高亮应独立选型**

SwiftMath/iosMath 的近亲是 AndroidMath：它明确是 iosMath 的 Kotlin 移植，使用原生 View 和 FreeType，不依赖 WebView。因此它比随机挑选一个 MathJax WebView wrapper 更贴近原来方案的设计。公开文档提供 `v1.1.0` 的 JitPack 接入示例，但维护与构建链仍需另行核验。[^19]

RaTeX 是更值得重点评估的新候选：Rust 解析和排版，输出 display list，由 Android Canvas 绘制，提供 Android 原生接入。Enriched RN 稳定包已经依赖它，因此并非只有一个孤立演示。其扩展公式能力和跨平台内核有吸引力；上游的 KaTeX 语法覆盖率、内存对比和“像素一致”表述不能替代对字体、基线、换行和截图的实际检查。[^6][^20]

推荐使用同一组公式比较 RaTeX、AndroidMath 和现有 SwiftMath：矩阵、分段函数、长分式、行内根式、中文混排、未闭合输入、错误表达式、超宽公式，以及深色模式。除了渲染成功，还应比较段落行高、点击放大、复制源码和 TalkBack 文本。

高亮分为两个场景。聊天代码块优先复用所选正文引擎已有高亮；Enriched 有 tree-sitter 接口，mikepenz 可使用 SnipMe Highlights。完整文件则需行号、搜索、跳转、水平滚动和大文本处理，Sora Editor 更贴近需求。它是 Android 代码编辑器，支持增量高亮、TextMate/tree-sitter、放大镜和搜索；可用只读模式，但编辑器能力也可能带来无用的包体和交互复杂度。[^21][^22]

不要把 tree-sitter 的存在等同于“整个 Markdown 已增量解析”，也不要把大文件编辑器全部嵌进每个聊天代码块。语言 grammar、字体和 native ABI 的成本应单独记录。Sora 使用 LGPL-2.1-or-later，其他候选也应逐项保留原始许可证与第三方 notices；本文不作整体许可兼容性的法律结论。[^22]

**8. 列表与输入框：由富文本宿主反推架构**

| 路线                                  | 适用条件                                 | 获得什么                                   | 需要验证什么                                     |
| ------------------------------------- | ---------------------------------------- | ------------------------------------------ | ------------------------------------------------ |
| RecyclerView + Android 原生 View 引擎 | 原生宿主是明确要求，富文本引擎可独立嵌入 | 显式复用、局部更新、原生选择和生命周期控制 | 活跃行重测、缓存、历史 prepend、视图回收         |
| Compose LazyColumn + Compose 正文     | 采用 mikepenz 或统一 Compose 控件        | 声明式局部状态、Material 集成、组件定制    | 稳定 key、重组范围、嵌套滚动、选择和测量         |
| FlashList v2 + Enriched RN            | 更重视直接使用成熟 RN 平台组件           | 减少自建 bridge，保留原生正文绘制          | JS/Fabric 更新成本、消息高度变化、键盘与列表配合 |

RecyclerView 的复用能力、Compose 的惰性布局和 FlashList v2 的位置保持都适合聊天，但不保证同一负载下同样快。FlashList v2 明确围绕 RN New Architecture 重写，并默认保持可见内容位置；这使它值得进入对照，而非未经测试就排除 RN 行宿主。[^23]

输入框方面，EditText 与 state-based Compose TextField 都是合理路线。后者管理文本、选择和 composing state，不应沿用“Compose 输入必然弱于 EditText”的预设。Lody 的真正工作仍是 IME composing 不被打断、附件与文字一起交接、失败恢复、模型菜单、多个宿主共享草稿和实际窗口 Insets。[^24]

原生宿主可使用 Insets/键盘动画 API；RN 宿主可评估 react-native-keyboard-controller 的聊天滚动方案。两条路线都必须明确唯一的键盘空间 owner，避免原生和 RN 重复避让。聊天页、新建会话 sheet、拖动关闭键盘、系统返回先关键盘再退页，都要单独验收。第三方富文本输入组件不能代替草稿事务层。[^25]

**9. Diff 与文件预览：保留已选好的强项**

Pierre 本身是 JS/React 文件与 Diff 渲染库，已经提供并排/上下布局、行内差异、Shiki 主题、换行、行号和选择等能力。没有找到证据足够充分、适用于当前项目且整体更强的 Android 原生替代。java-diff-utils 是差异计算和 patch 处理库，不是一整套等价 Diff UI。[^26]

建议保留全屏 Pierre，补 Android WebView 宿主，并把预热、复用、主题切换、资源生命周期和销毁纳入设计。当前仓库的 vendored DOM WebView 只注册 Apple，不能直接认为 Android 可用。预热收益要和后台内存压力一起衡量；数据引擎与 Diff 视图的 owner 必须独立，不能让关闭 Diff 销毁数据运行时。[^27]

工具详情里的短 Diff 可继续原生渲染，完整文件视图另评估 Sora。远端目录树保留已有 Machine RPC 模型和按需加载，不需要把一个本地存储文件管理器接入业务层。

Quick Look 没有单一完整替身。建议把统一“预览文件”的产品接口映射为：代码/Markdown 原生预览、Coil 图片、AndroidX PDF、其他 MIME 类型系统打开。Coil 支持内存/磁盘缓存与 Android/Compose 集成；PDF 组件应按最终最低版本和 SDK extension 要求核验，不承诺全设备统一支持。系统外部应用不可用时，也需要产品可理解的下载或分享入口。[^28]

**10. 数据引擎：JavaScriptSandbox 是值得认真研究的替代**

Lody 使用 WebView 不仅因为需要 JavaScript，还因为运行时依赖 WASM、StreamsClient、Web Crypto、AbortSignal、定时器和字节编码等能力。原生宿主负责授权请求、投影落盘、恢复和命令分发；它与聊天显示层的 JS 不是同一个职责。[^29]

| 路线                                 | 与现有代码的距离           | 优势                                                      | 主要缺口                                                   |
| ------------------------------------ | -------------------------- | --------------------------------------------------------- | ---------------------------------------------------------- |
| Android WebView                      | 最近                       | 保留浏览器环境和现有 bundled JS/WASM                      | 离屏生命周期、内存回收、桥接、来源/CORS、系统 WebView 差异 |
| Jetpack JavaScriptSandbox            | 中等，取决于运行时拆分程度 | 无需 WebView 视图，独立进程 isolate、终止回调、大字节输入 | 不是完整浏览器；Web API 和 I/O 适配必须验证                |
| Kotlin 网络 + Sandbox 中纯 CRDT/投影 | 更远                       | 更清晰的后台 owner 与计算边界                             | 重新实现 Streams 传输适配，建立协议一致性测试              |
| Loro Rust/FFI 原生化                 | 最远                       | 可减少浏览器依赖                                          | Loro 不等于 Flock + Streams + Machine RPC 全套             |

官方 JavaScriptEngine 已有稳定版本 `1.1.0`。它明确面向非交互 JS 计算，支持 WASM 和独立进程执行，可以由 Activity 或 Service 持有；需检测 API 26+ 设备上的实际 WebView provider 支持情况，以及每个所需 feature。无 View 带来的资源优势有官方设计依据，但节省多少内存必须实测。[^30]

**最有价值的原型不是只跑 `1 + 1`。** 应加载项目实际 Loro/Flock 产物，走 bootstrap、frame 解码、apply、投影输出，覆盖 8 MiB 输入边界、最大投影结果、isolate 被终止与账号切换。该引擎提供大输入和可选的 transaction-limit 能力，输出尺寸同样要验证，不能只确认 WASM instantiate 成功就宣布兼容。[^31]

对 `fetch`/ReadableStream、Web Crypto、TextEncoder/Decoder、AbortSignal 和定时器，应建立依赖清单逐项探测。现有官方引擎文档没有承诺完整浏览器环境，不能从“支持 WASM”推导当前 runtime 可以原封不动运行。若大量 polyfill 和双向调用成为主要成本，把网络/加密留给 Kotlin、Sandbox 只跑纯数据核心更合理，但这会扩大移植范围。[^29][^31]

原生 Loro FFI 可作为后续方向。官方存在 `loro-ffi`，但此次没有核验到能直接满足当前 Flock `0.4.3`、Loro `1.15.1`、StreamsClient `0.7.0` 全部契约的 Android SDK。QuickJS Kotlin 绑定提供 JS 执行能力，并不构成已验证的现有 WASM/browsers API 宿主。因此都不宜先于真实资产验证进入产品。[^32]

建议将 WebView 作为兼容对照，JavaScriptSandbox 作为潜在更优路线；两者使用同一份无凭据 fixture 和投影期望值。最终由兼容性、恢复可靠性、内存和维护边界共同决定，不预设 Android 必须复制 WKWebView 的实现形式。

**11. 后台执行与恢复不是一个组件能包办的功能**

当前 Swift 会区分应用后台暂停与 watchdog 故障，用户发起的 send 才关联 continued processing。Android 同样要区分前台实时同步、用户正在进行的发送/回复同步，以及应用长期不在前台时的补同步。不要把 README 的后台同步理解为无限常驻在线。[^29]

Kotlin 层继续承担 watchdog、generation fencing、有限重启与退出清理。任务恢复只能恢复读取和投影，不能自动重放发送；服务器 ACK 仍只表示交付，不能当作模型回复完成。凭据和账号变化必须销毁旧授权上下文。

前台服务只是受约束的续行机制，需要使用符合任务用途的 service type 和可见通知；不能因为“聊天”两个字就假定 `remoteMessaging` 一定合适。针对相应 target 的 Android 15+ `dataSync` 后台服务有累计时限，Android 16 起长时 WorkManager 工作还可能消耗 job quota；WorkManager 不是实时长连接的同义词。[^33]

建议的产品默认是前台实时、用户任务有限续行、通知提示与返回补同步。若必须保证长时间后台接收，则应作为独立需求验证 FGS 类型、系统限制和目标厂商行为；Sandbox 也不会绕过这些规则。

**12. SQLite、认证、Keychain 与推送**

当前 SQLite 存的是显示投影与恢复上下文，表结构很小，并不是完整 relational domain 或第二套 CRDT 数据库。Android 可以先保留同样的 key/value SQL 结构；当需要复杂查询和 schema 管理时再引入 Room。Room 的 SQL 检查和迁移能力有价值，但不会自动提高这种小表的冷启动速度。SQLDelight 也不是在仍保留 Swift owner 的情况下自动减少工作的选择。[^34]

Device Flow 继续使用官方注册客户端，不引入桌面凭据或新身份假设。Android 系统浏览器入口负责展示授权页面，RN/原生按既有 auth contract 处理取消和返回；安全存储保留在 LodyKit facade 内。

Android Keystore 保护加密密钥；token 应经该密钥加密后存到应用私有区域。它与 Apple Generic Password Keychain 的 API 不同，硬件 backing 要按实际 key/device 判断。强制每次解密弹出生物认证也不等价于当前 `AfterFirstUnlockThisDeviceOnly` 行为，会改变后台使用能力。备份恢复、重装、密钥失效和退出清理需要一起设计。[^35]

不建议基于旧文章新引入 EncryptedSharedPreferences 作为默认“最佳实践”：AndroidX Security Crypto 已弃用其 API，官方指向平台 API 和直接使用 Keystore。[^36]

推送优先保留 OneSignal Android。其官方平台支持 FCM、HMS、ADM 等配置入口，但 iOS 的 APNs 配置不能直接复用到 Android。需要在正式接入时明确目标设备是否包含无 GMS 环境。SDK 初始化、点击缓存、JS 确认和账号 fencing 应保持当前语义；不要把 OEM 推送差异藏成静默失败。[^37]

**13. 原生导航、系统外观和本地化**

保留 Expo Router NativeTabs、每个 tab 的 Stack 和 `definePage / present()`。Android 返回和 sheet 关闭必须产生与 iOS 同样可预期的 completed/cancelled 结果。Expo 文档已描述 Android 的原生 tab 与 bottom-sheet 行为，但页面间对 formSheet 的描述存在版本差异，必须按本项目固定的 Expo 57 / screens 版本验证；不能承诺所有 iOS sheet header 和嵌套 stack 选项在 Android 完全相同。[^38]

UIKit soft scroll edges、Liquid Glass、SF Symbols 不适合做机械效果复制。Android 采用 Material 原生顶栏、表面层级、触摸反馈和语义图标；这部分可参考官方 Material 组件与 Android 产品，但保持 Lody 蓝色操作、无绿色背景的约束。Material 动态配色可能产生绿色，因此不能默认把壁纸配色全部引入。图标 API 应接收语义名称，由平台映射，而不是要求 Android 解释 SF Symbol 字符串。[^39]

语言仍以 `apps/mobile/locales` 为单一来源，分别生成 Android strings/plurals 和 iOS xcstrings；格式占位符、复数规则、换行和引号转义需要平台适配。系统字体与 TalkBack 取代 SF 字体和 VoiceOver 的具体实现，但保留原生文本缩放和可访问名称，不增加只为复制 iOS 外观而存在的装饰层。

**14. 维护质量和发布可用性**

| 候选                    | 本次核实状态                                             | 对采用的含义                                            |
| ----------------------- | -------------------------------------------------------- | ------------------------------------------------------- |
| Enriched RN             | npm `1.0.2`；发布包已读取；主分支 2026-09-08 有更新；MIT | 功能有发布依据，但主分支改动不能默认算进稳定版          |
| Enriched Android SDK    | Maven `0.1.0`；独立功能表仍有缺口                        | 不能当作 RN 引擎的完整原生拆分版                        |
| mikepenz                | Maven `0.45.0`；主分支 2026-09-08；Apache-2.0            | 活跃候选，需核对 Kotlin/Compose/Java 与 Expo 工具链兼容 |
| react-native-streamdown | npm `0.3.0`；Worklets >= `0.10.0`；MIT                   | 可选的 Markdown 修补层，不是聊天调度和原生引擎          |
| Markwon                 | release `4.6.2`；检出默认分支日期 2021-03-15；Apache-2.0 | 成熟传统路线，维护信号弱，降低优先级                    |
| RikkaHub                | 固定源码 revision 日期 2026-09-09；AGPL-3.0 文档标示     | 适合产品参考；不当作通用 UI SDK                         |
| RaTeX                   | Enriched 稳定包实际接入 `0.1.10`；MIT                    | 有集成证据，公式显示与包体仍需测                        |
| Sora                    | 官方文档明确持续缓慢开发；LGPL-2.1-or-later              | 功能强，发布、ABI 和选择行为需对最终版本验证            |
| JavaScriptEngine        | 官方稳定 `1.1.0`；依赖 provider 能力                     | 官方维护并不表示所有设备具备所有 feature                |

react-native-streamdown 值得特别区分：它用 remend 修补未完成 Markdown，并可通过 Worklets 处理；渲染能力来自 Enriched。其 README 涉及 Worklets Bundle Mode、Metro 生成模块索引与生产 bundle 配置。这是与当前 pnpm monorepo、Metro 和离线 bundle 检查直接相关的集成成本。若 Lody 的原生节流和 Enriched 自身 streaming filter 已够用，不必再默认增加这一层。[^40]

对包含 md4c、tree-sitter、RaTeX 或 Sora native 依赖的最终组合，应检查 ABI、16 KiB page-size 兼容、发布包 native 资产、R8、NDK 与包体；这些是进入 Android 构建时的待办，不是本次已通过的验收。版本和许可证清单应在依赖锁定后由项目的 notices 流程生成。

**15. 建议的比较原型与淘汰条件**

先做可比较的质量证据，再选架构。建议的第一轮范围是三组原型，不扩散成完整 Android 产品开发。

| 原型                     | 最小内容                                             | 明确淘汰条件                                                  |
| ------------------------ | ---------------------------------------------------- | ------------------------------------------------------------- |
| A：Enriched Android 行为 | 发布包的正文、表格、公式、代码，放入一个真实虚拟列表 | 文本修正闪旧内容；完成后选择无法满足需求；队列持续积压        |
| B：mikepenz + 公式       | stable/tail 解析、服务端修正适配、复杂内容选择       | 语义与完整解析不一致；已完成内容持续重组/重测；公式集成过重   |
| C：WebView / Sandbox     | 真实 bundled Flock/Loro 输入、投影、销毁恢复         | 真实 API 不兼容；大数据通信失败；恢复出现重复写入或旧账号事件 |

所有原型使用无登录、无网络依赖的确定性数据。聊天输入应包含普通中文、emoji 家庭/肤色组合、组合重音、RTL、嵌套列表、表格、未闭合代码、稍后出现的引用定义与公式。至少回放普通小增量、48/256 字符突发、长回复、全文替换、相同长度修正，以及完成事件先于显示尾部结束等情况。

列表用同一份长历史，验证顶部补页、用户上翻、图片迟到导致高度变化、选择后滚出屏幕、来回进入聊天页、sheet 草稿恢复。要检查“最后显示内容与 authoritative 文本一致”，不能只看动画视频觉得顺滑。

性能采用 release/benchmark 构建，记录帧耗时分布与 jank、解析次数、稳定块重测次数、峰值内存、后台任务积压和冷启动投影时间。60 Hz 的单帧预算约 16.7 ms，120 Hz 约 8.3 ms；预算用于解释结果，不预先承诺所有设备都能达标。Macrobenchmark、Perfetto/JankStats 与 UI Automator 能分别提供性能和行为证据，截图用于视觉，视频用于时间行为。[^41]

建议设备至少包含一台中档 60 Hz、一台 120 Hz 和一个非 Pixel 厂商环境。模拟器适合协议、生命周期与自动化，不单独用于宣布最终流式性能。若产品要覆盖无 GMS 设备，需要另列推送与 WebView provider 验证。

**16. 研究后的选型意见**

优先对 Enriched Markdown 的完整 RN Android 引擎做等价性验证，并把 mikepenz 的增量解析路线保留为真正的竞争方案。两者分别更强在原生富文本交互的现成覆盖和稳定/尾部解析结构；目前证据不足以将任意一方定为全面赢家。独立 Kotlin Enriched SDK 的功能差距必须显式计入，不能以暂未实现的 roadmap 能力规划首版。

数学优先比较 RaTeX 和 AndroidMath；完整文件优先评估 Sora；全屏 Diff 保留 Pierre。数据层让 JavaScriptSandbox 与 WebView 用真实资产对照，优先考虑更清晰的 owner 和恢复行为。原生导航、输入、存储和推送使用 Android 合适的系统能力，保留 Lody 的业务契约。

这些候选都不要求移除已完成的 iOS 优化。共享的是模型、协议契约、展示状态语义和验收内容；平台层可以使用不同的最佳实现。正式采用哪个列表与富文本组合，应由上述原型结果决定。

**来源与固定源码索引**

以下来源均核验于 2026-09-09；动态文档按核验时内容解释，源码链接尽可能固定 commit。发布日期仅在正文有明确核验时使用。编号同时作为文中脚注。

[^1]: Lakr233，MarkdownView README 与包依赖：[README](https://github.com/Lakr233/MarkdownView/blob/4abc4817fa5211f05e25fbf7a6295fb8e9fcfd90/README.md)、[Package.swift](https://github.com/Lakr233/MarkdownView/blob/4abc4817fa5211f05e25fbf7a6295fb8e9fcfd90/Package.swift)。移动排版取舍、SwiftMath、Highlightr、cmark。

[^2]: Lakr233 / Litext contributors，[Litext README](https://github.com/Lakr233/Litext/blob/097475a348ab4a0aee1d027789307ebf69afbc1f/README.md)。CoreText、选择和绘制扩展能力。

[^3]: Lody 当前源码：[ChatMarkdownStore](../../apps/mobile/modules/lody-kit/ios/Chat/ChatMarkdownStore.swift)、[ChatMarkdownView](../../apps/mobile/modules/lody-kit/ios/Chat/ChatMarkdownView.swift)、[ChatTextFade](../../apps/mobile/modules/lody-kit/ios/Chat/ChatTextFade.swift)、[ChatFadeLabelView](../../apps/mobile/modules/lody-kit/ios/Chat/ChatFadeLabelView.swift)、[ChatStream](../../apps/mobile/modules/lody-kit/ios/Chat/ChatStream.swift)、[注入点设计](../superpowers/specs/2026-09-07-markdown-view-design.md)。路径对应本文本地 revision。

[^4]: Software Mansion，[Enriched Markdown 平台兼容表](https://enriched.swmansion.com/markdown/)。RN、独立 Kotlin、Swift 入口的功能区别。

[^5]: Software Mansion，[独立 Android SDK README](https://github.com/software-mansion/enriched-markdown/blob/bd2fbf09e23ed74de8329c874aa0c5037595a2c8/packages/enriched-markdown-android/README.md)；[Maven 元数据](https://repo.maven.apache.org/maven2/com/swmansion/enriched/markdown/compose/maven-metadata.xml)。独立包 `0.1.0`、minSdk 24、Compose/AndroidView 接口。

[^6]: Software Mansion，[RN npm 1.0.2 元数据](https://registry.npmjs.org/react-native-enriched-markdown/1.0.2)、[实际发布包](https://registry.npmjs.org/react-native-enriched-markdown/-/react-native-enriched-markdown-1.0.2.tgz)、[1.0.2 发布说明](https://swmansion.com/changelog/react-native-enriched-markdown-1-0-2/)。SHA-256 与关键文件差异见证据 JSON。

[^7]: Software Mansion，[SegmentReconciler](https://github.com/software-mansion/enriched-markdown/blob/bd2fbf09e23ed74de8329c874aa0c5037595a2c8/packages/react-native-enriched-markdown/android/src/main/java/com/swmansion/enriched/markdown/segments/SegmentReconciler.kt)、[ContainerNodeView](https://github.com/software-mansion/enriched-markdown/blob/bd2fbf09e23ed74de8329c874aa0c5037595a2c8/packages/react-native-enriched-markdown/android/src/main/java/com/swmansion/enriched/markdown/segments/ContainerNodeView.kt)。发布包同类逻辑位于 `utils/common/SegmentReconciler.kt`。

[^8]: Software Mansion，[TailFadeInAnimator](https://github.com/software-mansion/enriched-markdown/blob/bd2fbf09e23ed74de8329c874aa0c5037595a2c8/packages/react-native-enriched-markdown/android/src/main/java/com/swmansion/enriched/markdown/utils/text/TailFadeInAnimator.kt)、[FadeInSpan](https://github.com/software-mansion/enriched-markdown/blob/bd2fbf09e23ed74de8329c874aa0c5037595a2c8/packages/react-native-enriched-markdown/android/src/main/java/com/swmansion/enriched/markdown/spans/FadeInSpan.kt)。Animator 文件与 npm 1.0.2 相同。

[^9]: Software Mansion，[EnrichedMarkdown 容器](https://github.com/software-mansion/enriched-markdown/blob/bd2fbf09e23ed74de8329c874aa0c5037595a2c8/packages/react-native-enriched-markdown/android/src/main/java/com/swmansion/enriched/markdown/EnrichedMarkdown.kt)。解析队列、分块、尾部和表格动画；稳定包另见来源 6。

[^10]: Mike Penz，[Maven 元数据](https://repo.maven.apache.org/maven2/com/mikepenz/multiplatform-markdown-renderer/maven-metadata.xml)、[MIGRATION](https://github.com/mikepenz/multiplatform-markdown-renderer/blob/3647f0f7a349068065baf9bb97854ddd43389eef/MIGRATION.md)、[README](https://github.com/mikepenz/multiplatform-markdown-renderer/blob/3647f0f7a349068065baf9bb97854ddd43389eef/README.md)。发布版本、streaming 入口与依赖变化。

[^11]: Mike Penz，[StreamingMarkdownState.kt](https://github.com/mikepenz/multiplatform-markdown-renderer/blob/3647f0f7a349068065baf9bb97854ddd43389eef/multiplatform-markdown-renderer/src/commonMain/kotlin/com/mikepenz/markdown/model/StreamingMarkdownState.kt)。append-only、AST、引用和调度行为。

[^12]: Mike Penz，[StreamingMarkdownStateTest.kt](https://github.com/mikepenz/multiplatform-markdown-renderer/blob/3647f0f7a349068065baf9bb97854ddd43389eef/multiplatform-markdown-renderer/src/commonTest/kotlin/com/mikepenz/markdown/model/StreamingMarkdownStateTest.kt)。源码测试覆盖范围。

[^13]: Android Developers，[SelectionContainer API](https://developer.android.google.cn/reference/kotlin/androidx/compose/foundation/text/selection/SelectionContainer.composable)。惰性布局中未创建文本的选择边界。

[^14]: Noties，[Markwon README](https://github.com/noties/Markwon/blob/2ea148c30a07f91ffa37c0aa36af1cf2670441af/README.md)、[插件列表](https://noties.io/Markwon/docs/v4/install.html)、[v4.6.2](https://github.com/noties/Markwon/releases/tag/v4.6.2)。默认分支 commit 日期来自固定 checkout。

[^15]: Halil Ozercan，[Compose Richtext Markdown](https://halilibo.com/compose-richtext/richtext-markdown/)；Mohamed Rejeb，[Compose Rich Editor](https://github.com/MohamedRejeb/Compose-Rich-Editor)。抽象与用途比较。

[^16]: RikkaHub，[Markdown.kt](https://github.com/rikkahub/rikkahub/blob/6e0aa7d486da3487acebc5e09e2a808603c1898a/app/src/main/java/me/rerere/rikkahub/ui/components/richtext/Markdown.kt)、[MarkdownNew.kt](https://github.com/rikkahub/rikkahub/blob/6e0aa7d486da3487acebc5e09e2a808603c1898a/app/src/main/java/me/rerere/rikkahub/ui/components/richtext/MarkdownNew.kt)、[依赖](https://github.com/rikkahub/rikkahub/blob/6e0aa7d486da3487acebc5e09e2a808603c1898a/gradle/libs.versions.toml)。定制解析与排版路径。

[^17]: RikkaHub，[ChatMessage.kt](https://github.com/rikkahub/rikkahub/blob/6e0aa7d486da3487acebc5e09e2a808603c1898a/app/src/main/java/me/rerere/rikkahub/ui/components/message/ChatMessage.kt#L418)。流式期间关闭 SelectionContainer 的实现。

[^18]: Lakr233，[FlowDown](https://github.com/Lakr233/FlowDown)；GetStream，[Android SDK](https://getstream.io/chat/docs/sdk/android/)；CometChat，[Android SDK](https://www.cometchat.com/docs/sdk/android/overview)。产品参考与 SDK 数据边界。

[^19]: Greg Cockroft，[AndroidMath](https://github.com/gregcockroft/AndroidMath)。iosMath 移植、FreeType、原生 View 和发布示例。

[^20]: erweixin，[RaTeX](https://github.com/erweixin/RaTeX)、[项目文档与对照](https://ratex.lites.dev/)。原生 Rust 排版、display list、支持范围；性能主张未在本文复测。

[^21]: SnipMe，[Highlights](https://github.com/SnipMeDev/Highlights)；Software Mansion，[Android 高亮和数学依赖配置](https://github.com/software-mansion/enriched-markdown/blob/bd2fbf09e23ed74de8329c874aa0c5037595a2c8/packages/react-native-enriched-markdown/android/build.gradle)。

[^22]: Rosemoe，[Sora Editor](https://github.com/Rosemoe/sora-editor)、[能力说明](https://project-sora.github.io/sora-editor-docs/guide/editor-overview)、[语言支持](https://project-sora.github.io/sora-editor-docs/guide/using-language)。开发状态与许可证以仓库说明为准。

[^23]: Android Developers，[RecyclerView](https://developer.android.com/develop/ui/views/layout/recyclerview)、[Compose lists](https://developer.android.com/develop/ui/compose/lists)；Shopify，[FlashList v2 设计](https://shopify.engineering/flashlist-v2)、[位置保持 API](https://github.com/Shopify/flash-list/blob/main/documentation/docs/fundamentals/usage.md)。

[^24]: Android Developers，[Configure text fields](https://developer.android.com/develop/ui/compose/text/user-input)。state-based TextField、选择和 composing state。

[^25]: Android Developers，[键盘 Insets 与动画](https://developer.android.com/develop/ui/views/layout/sw-keyboard)；Keyboard Controller，[Building a chat app](https://kirillzyusko.github.io/react-native-keyboard-controller/docs/guides/building-chat-app)。

[^26]: Pierre，[Diffs](https://github.com/pierrecomputer/pierre/tree/main/packages/diffs)；java-diff-utils，[项目说明](https://github.com/java-diff-utils/java-diff-utils)。展示层与差异计算层的能力区别。

[^27]: Lody，[DOM WebView 注册](../../packages/dom-webview/expo-module.config.json)、[SharedDiffWebView](../../packages/dom-webview/ios/SharedDiffWebView.swift)、[复用设计](../superpowers/specs/2026-09-08-reusable-diff-rendering-design.md)。

[^28]: Coil，[Image loaders](https://coil-kt.github.io/coil/image_loaders/)；Android Developers，[PdfViewerFragment](https://developer.android.com/reference/androidx/pdf/viewer/fragment/PdfViewerFragment)。组件能力与平台条件。

[^29]: Lody，[data-runtime](../../apps/mobile/modules/lody-kit/data-runtime/index.ts)、[Machine RPC 加密](../../apps/mobile/modules/lody-kit/data-runtime/machine-rpc.ts)、[DataRuntime.swift](../../apps/mobile/modules/lody-kit/ios/Cloud/DataRuntime.swift)、[ContinuedSessionTasks](../../apps/mobile/modules/lody-kit/ios/Cloud/ContinuedSessionTasks.swift)。

[^30]: Android Developers，[JavaScriptEngine releases](https://developer.android.com/jetpack/androidx/releases/javascriptengine)、[Executing JavaScript and WebAssembly](https://developer.android.com/develop/ui/views/layout/webapps/jsengine)。稳定版本与宿主能力。

[^31]: Android Developers，[JavaScriptIsolate API](https://developer.android.com/reference/androidx/javascriptengine/JavaScriptIsolate)、[JavaScriptSandbox API](https://developer.android.com/reference/androidx/javascriptengine/JavaScriptSandbox)。大字节输入、可选 feature 与返回边界；不是浏览器 API 完整性承诺。

[^32]: Loro，[loro-ffi](https://github.com/loro-dev/loro-ffi)、[Getting Started](https://www.loro.dev/docs/tutorial/get_started)；dokar3，[quickjs-kt](https://github.com/dokar3/quickjs-kt)。尚未验证成套 Lody runtime 兼容。

[^33]: Android Developers，[Foreground service types](https://developer.android.com/develop/background-work/services/fgs/service-types)、[Timeouts](https://developer.android.com/develop/background-work/services/fgs/timeout)、[Long-running workers](https://developer.android.com/develop/background-work/background-tasks/persistent/how-to/long-running)。

[^34]: Lody，[LocalStore.swift](../../apps/mobile/modules/lody-kit/ios/Cloud/LocalStore.swift)；Android Developers，[SQLite](https://developer.android.com/training/data-storage/sqlite)、[SQLite 到 Room](https://developer.android.com/training/data-storage/room/sqlite-room-migration)。

[^35]: Android Developers，[Keystore system](https://developer.android.com/privacy-and-security/keystore)；Lody，[AuthKeychain.swift](../../apps/mobile/modules/lody-kit/ios/Auth/AuthKeychain.swift)。

[^36]: Android Developers，[Security Crypto release notes](https://developer.android.com/jetpack/androidx/releases/security#security-crypto)。API 弃用与迁移方向。

[^37]: OneSignal，[Mobile SDK setup](https://documentation.onesignal.com/docs/en/mobile-sdk-setup)、[Android SDK setup](https://documentation.onesignal.com/docs/en/android-sdk-setup)、[Huawei setup](https://documentation.onesignal.com/docs/en/huawei-sdk-setup)。

[^38]: Expo，[Native tabs](https://docs.expo.dev/versions/latest/sdk/router/native-tabs/)、[Modals](https://docs.expo.dev/router/advanced/modals/)、[Router API](https://docs.expo.dev/versions/latest/sdk/router/)。版本相关能力需要按锁定依赖复核。

[^39]: Android Developers，[Compose Material 3 releases](https://developer.android.com/jetpack/androidx/releases/compose-material3)；Material Components，[AppBar/Search](https://github.com/material-components/material-components-android/blob/master/docs/components/Search.md)。

[^40]: Software Mansion Labs，[react-native-streamdown README](https://github.com/software-mansion-labs/react-native-streamdown/blob/8bff19a6cb8f549c0ca4758618c398d9d056ac5c/README.md)、[hook 实现](https://github.com/software-mansion-labs/react-native-streamdown/blob/8bff19a6cb8f549c0ca4758618c398d9d056ac5c/src/hooks/useStreamdownMarkdown.ts)、[npm 0.3.0 元数据](https://registry.npmjs.org/react-native-streamdown/0.3.0)。

[^41]: Android Developers，[Macrobenchmark](https://developer.android.com/topic/performance/benchmarking/macrobenchmark-overview)、[JankStats](https://developer.android.com/topic/performance/jankstats)、[Baseline Profiles 示例](https://developer.android.com/codelabs/android-baseline-profiles-improve)。用于后续验证，本文没有报告实测成绩。
