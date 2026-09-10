# Android bundled data runtime

PR-02 implementation notes, 2026-09-10. The host passed the documented local emulator checks; stage B and product authentication are not complete. See [verification evidence](../research/android-wasm-verification.md).

**Ownership and assets**

`LodyKitModule` owns the internal verification run. Kotlin `DataRuntime` owns one offscreen WebView, pending command callbacks, bounded bridge admission and destruction. Every WebView operation runs on the main thread; Android bridge calls assemble messages on the bridge thread before handing complete events to main. Production account/workspace lifecycle, watchdog recovery and secure storage follow in PR-03/04/09.

`build-decoder.mjs` compiles the existing runtime once and copies the exact HTML and Loro/Flock license bytes to both native resource locations. The Android asset directory is generated, ignored by Git and rebuilt by `native:assets`. No independent Android decoder implementation replaces Streams or the existing CRDT code.

The WebView opens only the app-provided `https://appassets.androidplatform.net/runtime.html` document, served directly from assets by its request handler. Navigation is rejected. File/content access and mixed content are disabled. The bundled CSP allows its inline code and WASM plus HTTPS connections, and disallows remote scripts and frames. Short-lived grants enter through native commands; the host does not own long-lived credentials.

The origin and threading choices follow Android's [local-content guidance](https://developer.android.com/develop/ui/views/layout/webapps/load-local-content) and [WebView bridge contract](<https://developer.android.com/reference/android/webkit/WebView#addJavascriptInterface(java.lang.Object,%20java.lang.String)>).

**Transport bounds**

- iOS retains `webkit.messageHandlers.dataRuntime.postMessage(object)`.
- Android JSON events use ordered 32 Ki UTF-16-code-unit chunks. Java acknowledges each chunk synchronously. Surrogate pairs may span chunks but are reassembled before JSON parsing.
- A message and the combined queued complete messages are each limited to 4 Mi UTF-16 code units; at most 16 complete messages await main-thread delivery. An invalid sequence, failed admission or excess size ends that runtime with `bridge_limit`.
- Native-to-JS commands contain a request ID, method and JSON argument array. They are limited to 64 Ki code units and 16 pending requests, with native 30-second deadlines. Close settles pending requests as stopped. The RPC error surface does not export exception strings containing request data.
- The existing 8 MiB catalog input ceiling is independent of these bridge bounds. Network response bodies stay inside WebView/JS; they do not pass through an RN copy of the CRDT replica. The Android host's projection ceiling is an explicit failure boundary, not a claim that all inputs below the catalog ceiling produce admissible projections.

**Offline proof boundary**

`DataRuntimeVerification` injects native HTTP responses while running the normal bundled page, actual `StreamsClient`, actual Flock/Loro WASM, frame parser and projectors. It blocks unknown requests and records writes; the read-only fixtures must make zero writes. Native response reads are fragmented to exercise browser body assembly. This tests transport fragmentation; it does not change the protocol rule that a logical update body contains complete length frames.

Fixtures cover Flock bootstrap plus framed incremental updates, a real Zstd-compressed snapshot, a multi-chunk catalog projection, a projection above the bridge output ceiling, truncated length/body and invalid JSON, input above 8 MiB, and actual Loro session history import. Catalog projections are compared structurally with the Node baseline from the same fixture, including Unicode content. Fixed compressed fixture bytes avoid requiring a Zstd encoder on older supported Node versions during builds.

The report records fixture/asset hashes, runtime HTML hash, projection counts, transported character/chunk counts, peak admitted queue size and HTTP read/write counts. The Android runner captures screen/video/log evidence and the installed WebView provider. Node bridge tests additionally exercise rejected admission and oversized output; they do not substitute for emulator checks.

The documented emulator and iOS native regression checks have passed; remote CI and evidence publication are tracked separately. Live Cloud authorization, write operations, lifecycle recovery, secure storage and physical-device performance are outside this PR's proof.
