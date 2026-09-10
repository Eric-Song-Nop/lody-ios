import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

const sdk = process.env.ANDROID_HOME ?? join(homedir(), 'Library/Android/sdk');
if (!existsSync(sdk))
  throw new Error('Set ANDROID_HOME to an installed Android SDK.');
const result = spawnSync(
  './gradlew',
  [':app:assembleRelease', '--no-daemon', '--console=plain'],
  {
    cwd: new URL('../android/', import.meta.url),
    stdio: 'inherit',
    env: { ...process.env, ANDROID_HOME: sdk, EXPO_PUBLIC_ANDROID_VERIFY: '1' },
  },
);
if (result.error) throw result.error;
process.exit(result.status ?? 1);
