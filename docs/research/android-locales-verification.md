# Android compiled language resources

PR-05b adds Android resources generated from the existing `apps/mobile/locales` JSON catalogs. The generator produces 101 native keys in default English and `values-b+zh+Hans`, collapsing `.one`/`.other` pairs into Android plurals. The iOS xcstrings generator remains in place.

Generation runs through both `native:assets` and the Android prebuild mod. `pnpm i18n:check` fails on stale resources. Kotlin resource IDs are generated explicitly, so resource shrinking does not depend on reflection. Native `LodyStrings` uses Android's quantity selection and then interpolates named parameters exactly once; argument contents remain literal. Missing keys, incorrect arguments and incorrect use of plural quantities fail explicitly. The close button uses the resource when the caller has not supplied an accessibility label and refreshes it on configuration changes.

Generator tests cover XML-sensitive characters, quotes, whitespace, backslashes, formatting-looking text, plural grouping, missing translations and normalized-name collisions. The device fixture reads every compiled resource using localized Android contexts for English, Simplified Chinese and Spanish fallback, including quantities 0/1/2. Its RN boundary compares each returned value with the shared source catalog and rejects missing or duplicate cases. It also checks four invalid native calls. This proves compiled resource lookup and interpolation, not a whole-app system-language switch or bilingual product acceptance.

Run `pnpm verify:android --case locales --appearance light --apk <internal.apk>`. The scene is offline and exposes only fixture text. Local screenshot/video/results remain under `.artifacts/android`; remote acceptance publication is separate. Build and emulator evidence are being collected. Broader system-font, TalkBack and product language coverage remain part of the unfinished PR-05 gate.

Reference: [Android string and quantity resources](https://developer.android.com/guide/topics/resources/string-resource).
