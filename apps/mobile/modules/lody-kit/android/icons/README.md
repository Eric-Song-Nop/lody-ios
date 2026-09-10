# Android semantic icons

Material Symbols from Google, obtained through better-icons/Iconify. `sources.json` records each downloaded source and SHA-256. The Apache-2.0 license is preserved in `../../licenses/MaterialSymbols-LICENSE.txt` and included by the app's license generator.

Run `python3 apps/mobile/modules/lody-kit/android/icons/convert.py` from the repository root to regenerate the committed Android vectors without network access. Conversion deliberately rejects unsupported SVG features rather than dropping them. Android builds consume the vectors directly from LodyKit; Expo prebuild does not erase this module.

`chrome/LodySymbols.kt` maps the current internal UI's semantic names to these resources. Unknown names are rejected; additional product screens must add their real semantic mappings before entering the Android graph. The present catalog is not a claim that every SF Symbol has an Android counterpart. NativeTabs use the same resources for selected and unselected states.
