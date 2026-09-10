# Lody iOS acceptance

## 1. Project summary

Expo Router iOS app in apps/mobile; UIKit capabilities live in LodyKit.

## 2. Environment

Use `pnpm start` for Metro. For a verified signed build, use the managed lease
wrapper below and pass `$LODY_VERIFY_UDID` as the xcodebuild destination; do not
use `pnpm ios`, which lets Expo select another Simulator. Check listening Node
processes before starting a server; do not stop servers owned by another task.
Metro currently uses 8081. Generate assets with
`pnpm --filter @lody-ios/mobile native:assets` before direct xcodebuild.

## 3. Auth

UI regression baselines use `pnpm verify:ui --app <Debug.app>` and automatically
lease an erased `Lody * Verify` Simulator. For a build plus multiple checks, use
`pnpm verify:simulator --name '<current verify>' -- <command>` and target
`$LODY_VERIFY_UDID`; nested verify commands reuse that lease. Never call
`simctl create` directly for local verification. Explicit `--udid` is reserved
for a caller-owned device such as CI, which also owns its cleanup.
The runner owns an isolated Metro with `EXPO_PUBLIC_UI_VERIFY=1`; account restoration
and login are disabled, and Debug scenes use production components with local fixtures.
No account, cloud credentials or connected machine is needed. See
`apps/mobile/verification/ui/README.md` for cases, evidence and CI setup.

Official Lody Device Flow and simulator Keychain only. Inspect the simulator UI for existing login; never copy desktop credentials. No seeded account is provided. Unauthenticated checks must be reported separately from authenticated flows.

## 4. Surfaces

Use AXe with explicit simulator UDID and simctl screenshots. Build workspace apps/mobile/ios/Lody.xcworkspace, scheme Lody, with normal signing. Bundle identifier app.innei.lody. Run pnpm check, pnpm test and pnpm bundle as supporting gates.

## 5. Project probes & quick navigation

`xcrun simctl list devices booted`; `axe describe-ui --udid <id>`. Product tabs are sessions, settings and search. Development-only Debug lives under Settings.

## 6. Known constraints

Cloud data requires app-authorized login and a connected computer. Do not send real turns merely to verify layout. Preserve all pre-existing working-tree edits. Simulator cannot prove physical haptics.

## Android staged verification

Android commands, dedicated AVD ownership and offline case details live in `apps/mobile/verification/android/README.md`. Use `pnpm build:android`, then `pnpm verify:android --case bootstrap --apk apps/mobile/android/app/build/outputs/apk/release/app-release.apk`. Only the completed stage cases may be claimed. The runner uses adb/UI Automator on an isolated app installation, saves local screenshot/video/state evidence and shuts down its owned emulator. A caller-owned serial authorizes resetting only this app. Never wipe an existing user AVD.
