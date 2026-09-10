# Android semantic symbol verification

PR-05b has 39 explicit LodyKit symbol mappings: the original 12 and 27 additions selected against existing Settings, Onboarding, session and tool activity call sites. Native symbols and symbol buttons use the same `LodySymbols` resource lookup. Unknown symbols still fail; remote avatar URLs are image inputs for their later owning product capability, not symbol names.

The additions use Material Symbols, retrieved with the installed Better Icons CLI. `modules/lody-kit/licenses/AndroidSymbols-sources.json` (under `apps/mobile`) records each added semantic name, Material ID, source URL, SVG hash and Android resource. The existing Apache license remains in `MaterialSymbols-LICENSE.txt`. Only simple monochrome 24×24 path SVGs were converted to compiled VectorDrawable resources; no runtime font, network download or new icon package is needed. Outline/filled variants remain distinct for folder, settings, circle and pin. Unpin uses the crossed pin; restore-from-archive uses unarchive; connection failure uses the octagonal X.

The offline `AndroidSymbolsScreen` renders the fixed corpus through production `NativeSymbol` and `NativeSymbolButton`, six names per batch. Button slots deliberately retain their React identity between batches to exercise native symbol and action rebinding. A visible action result records the current semantic name. The screen is reachable through `present` in the Android verification page and sheet hosts; it opens no product routes or cloud data.

`pnpm verify:android --case symbols --symbols-host page|sheet --appearance light|dark --apk <internal.apk>` checks the full corpus, 48 dp targets, one current-ID action per batch, the final disabled Next action and actual Back dismissal in the selected host. Run each host and appearance separately to keep the full recording within its time limit. It captures every batch, the native hierarchy and recording. Captions or successful resource lookup alone do not prove correct glyph shapes: each captured pair of static/action icons requires visual review, including meaningful outline/filled and pin/unpin differences.

Status: `pnpm check`, iOS Metro bundle and Python runner syntax checks pass at the recorded catalog revision. The Android build containing `c226ef1` now passes in 4m 59s; APK SHA-256 is `3382ae3edf3f4ebd1c53236af449bcc99a3c7f7b31873adb51ceb0cd590a9d38`. Build started at `c1a5752` with documentation edits; later commits only update reports/checklists. The first page/light device run passes; remaining hosts/themes are running sequentially. The corresponding normally signed iOS build, the full host/theme matrix, glyph visual review and affected navigation/controls checks remain pending. The completed `c7760795…` list matrix predates these icon changes and cannot establish symbol acceptance. Full PR-05b remains incomplete.

## First device result: page, light

API 36 ARM64, `symbols-v1`, runner `2564677` with a clean checkout; APK `3382ae3e…` above. All 39 button bounds meet 48 dp, each of seven reused-button activations reports the current semantic name, the final Next button is disabled, and system Back removes the host. The runner restores night mode and shuts down its owned emulator.

All eight screenshots (boot plus seven batches) and the full 91.957833-second recording sampled every five seconds have been reviewed. Static and action glyphs match, filled/outline and pin/unpin variants remain distinguishable, and archive/restore, document search, security and error shapes retain the intended meaning. The sampled recording ends on the final catalog batch; host removal is established by the runner's hierarchy assertion, not that final sampled frame.

Evidence: `.artifacts/android/symbol-catalog-page-light`, including `result.json`, all seven batch hierarchies/images, `symbols.mp4` and `visual-review.json`. This result covers one host/theme only; TalkBack and the remaining matrix are not accepted by this result.

## Light sheet result

The same `3382ae3e…` APK passes `symbols-v1` in the light sheet host. Runner checkout was `2564677` with documentation changes. All 39 targets meet 48 dp, all seven sampled reused-button actions return the current name, final Next is disabled and Back removes the host. Night mode is restored and the owned emulator is shut down.

All eight screenshots and the complete 101.864400-second recording sampled every five seconds are reviewed in `.artifacts/android/symbol-catalog-sheet-light`. Glyph semantics and outline/filled distinctions match the page result; long labels and buttons remain readable below the native sheet header. The sampled recording ends on the final catalog batch, so it does not itself prove dismissal. Both light hosts now have scoped device evidence; dark hosts and TalkBack remain pending.
