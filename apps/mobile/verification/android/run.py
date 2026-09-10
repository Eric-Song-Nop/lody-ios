#!/usr/bin/env python3
"""Run explicit offline Android cases on a caller-owned device or a leased AVD."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
SDK = Path(os.environ.get('ANDROID_HOME', Path.home() / 'Library/Android/sdk'))
PACKAGE = 'app.innei.lody'


def command(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, timeout=kwargs.pop('timeout', 60), **kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--case', choices=['bootstrap', 'wasm'], required=True)
    parser.add_argument('--adb-port', type=int, default=5038, help='Dedicated SDK adb server; leaves the default 5037 server alone.')
    parser.add_argument('--serial', help='Caller-owned device; installs and clears only app.innei.lody.')
    parser.add_argument('--avd', default='Lody_Android_Verify_36')
    parser.add_argument('--gpu', choices=['auto', 'host', 'software'], default='host')
    parser.add_argument('--memory-mb', type=int, default=4096, help='RAM for the owned emulator; does not modify its saved AVD configuration.')
    parser.add_argument('--avd-home', type=Path, help='AVD registry directory when SDK tools use a different default.')
    parser.add_argument('--output', type=Path, default=ROOT / '.artifacts/android' / time.strftime('%Y%m%d-%H%M%S'))
    args = parser.parse_args()
    if args.memory_mb < 2048:
        parser.error('--memory-mb must be at least 2048.')
    if not args.apk.is_file():
        parser.error('APK does not exist; run pnpm build:android first.')
    args.output.mkdir(parents=True, exist_ok=False)
    adb = SDK / 'platform-tools/adb'
    adb_command = [str(adb), '-P', str(args.adb_port)]
    emulator = None
    emulator_log = None
    recorder_pid = None
    serial = args.serial
    result = {'apkSha256': hashlib.file_digest(args.apk.open('rb'), 'sha256').hexdigest(), 'case': args.case, 'status': 'failed', 'checks': [], 'commit': command(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
    result['workingTreeDirty'] = bool(command(['git', 'status', '--porcelain'], cwd=ROOT, capture_output=True, text=True).stdout.strip())
    result['fixtureVersion'] = 'bootstrap-v1'

    def shell(*parts):
        return command([*adb_command, '-s', serial, 'shell', *parts], capture_output=True, text=True).stdout.strip()

    def snapshot():
        shell('uiautomator', 'dump', '/sdcard/lody-verify.xml')
        xml = shell('cat', '/sdcard/lody-verify.xml')
        return ET.fromstring(xml)

    def texts(tree):
        return '\n'.join(node.get('text', '') for node in tree.iter('node'))

    def wait_text(expected, timeout=30):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            tree = snapshot()
            if 'WASM failed:' in texts(tree):
                raise AssertionError(texts(tree))
            if expected in texts(tree):
                return tree
            time.sleep(0.5)
        raise AssertionError(f'Missing UI state: {expected}')

    def capture(name):
        with (args.output / f'{name}.png').open('wb') as file:
            command([*adb_command, '-s', serial, 'exec-out', 'screencap', '-p'], stdout=file)
        (args.output / f'{name}.xml').write_text(ET.tostring(snapshot(), encoding='unicode'))

    def foreground():
        shell('input', 'keyevent', 'KEYCODE_HOME')
        time.sleep(1)
        shell('am', 'start', '-W', '-n', f'{PACKAGE}/.MainActivity')

    def tap_button(tree, title):
        button = next(node for node in tree.iter('node') if node.get('text', '').lower() == title.lower())
        x1, y1, x2, y2 = map(int, re.findall(r'\d+', button.attrib['bounds']))
        shell('input', 'tap', str((x1 + x2) // 2), str((y1 + y2) // 2))

    try:
        command([*adb_command, 'start-server'], capture_output=True)
        server = command([*adb_command, 'server-status'], capture_output=True, text=True).stdout
        if str(adb.resolve()) not in server:
            raise RuntimeError('Dedicated adb port is owned by another binary; choose --adb-port.')
        result['adbServerPort'] = args.adb_port
        if not serial:
            avd_home = args.avd_home
            if avd_home is None and not os.environ.get('ANDROID_AVD_HOME'):
                candidates = [Path.home() / '.android/avd', Path.home() / '.config/.android/avd']
                matches = [path for path in candidates if (path / f'{args.avd}.ini').is_file()]
                if len(matches) != 1:
                    raise RuntimeError('Specify --avd-home: dedicated AVD registry is missing or ambiguous.')
                avd_home = matches[0]
            emulator_env = dict(os.environ)
            emulator_env['ANDROID_ADB_SERVER_PORT'] = str(args.adb_port)
            if avd_home:
                emulator_env['ANDROID_AVD_HOME'] = str(avd_home.resolve())
            avds = command([SDK / 'emulator/emulator', '-list-avds'], env=emulator_env, capture_output=True, text=True).stdout.splitlines()
            if args.avd not in avds:
                raise RuntimeError(f'Create the dedicated AVD {args.avd} as documented; existing user AVDs are never erased.')
            devices = command([*adb_command, 'devices'], capture_output=True, text=True).stdout
            for port in range(5580, 5680, 2):
                if f'emulator-{port}' in devices:
                    continue
                with socket.socket() as probe:
                    if probe.connect_ex(('127.0.0.1', port)) == 0:
                        continue
                serial = f'emulator-{port}'
                break
            else:
                raise RuntimeError('No emulator port available.')
            emulator_log = (args.output / 'emulator.log').open('w')
            result['emulator'] = {'avd': args.avd, 'gpu': args.gpu, 'memoryMb': args.memory_mb}
            emulator = subprocess.Popen([str(SDK / 'emulator/emulator'), '-avd', args.avd, '-port', str(port), '-no-snapshot', '-gpu', args.gpu, '-memory', str(args.memory_mb), '-no-boot-anim', '-no-audio'], stdout=emulator_log, stderr=subprocess.STDOUT, env=emulator_env)
            deadline = time.monotonic() + 180
            while time.monotonic() < deadline:
                if emulator.poll() is not None:
                    raise RuntimeError('Emulator exited; inspect emulator.log.')
                probe = subprocess.run([*adb_command, '-s', serial, 'shell', 'getprop', 'sys.boot_completed'], capture_output=True, text=True, timeout=10)
                if probe.returncode == 0 and probe.stdout.strip() == '1':
                    break
                time.sleep(1)
            else:
                raise TimeoutError('Emulator did not boot in 180 seconds.')
        result['serial'] = serial
        result['system'] = shell('getprop', 'ro.build.fingerprint')
        result['abi'] = shell('getprop', 'ro.product.cpu.abi')
        command([*adb_command, '-s', serial, 'install', '-r', args.apk], capture_output=True, text=True)
        shell('pm', 'clear', PACKAGE)
        shell('input', 'keyevent', 'KEYCODE_WAKEUP')
        shell('wm', 'dismiss-keyguard')
        recorder_pid = shell('sh', '-c', f"'screenrecord --time-limit 180 /sdcard/lody-verify-{args.case}.mp4 >/dev/null 2>&1 & echo $!'")
        if not recorder_pid.isdigit():
            raise RuntimeError(f'Could not start screenrecord: {recorder_pid}')
        shell('am', 'start', '-W', '-n', f'{PACKAGE}/.MainActivity')
        tree = wait_text('LodyKit: Android')
        capture('boot')
        if args.case == 'wasm':
            result['webViewProvider'] = shell('dumpsys', 'webviewupdate')
            tap_button(tree, 'Run WASM verification')
            wait_text('WASM passed:', timeout=180)
            command([*adb_command, '-s', serial, 'pull', f'/sdcard/Android/data/{PACKAGE}/files/lody-runtime-verification.json', args.output / 'runtime.json'], capture_output=True)
            runtime = json.loads((args.output / 'runtime.json').read_text())
            required = {'increment', 'compressed', 'large', 'output-limit', 'truncated-length', 'truncated-body', 'invalid-json', 'over-limit'}
            actual = {case['name'] for case in runtime['cases'] if case['status'] == 'pass'}
            if actual != required:
                raise AssertionError(f'Runtime case coverage mismatch: {actual}')
            result['fixtureVersion'] = runtime['fixtureVersion']
            result['checks'] = runtime['cases']
            capture('wasm-passed')
        else:
            result['checks'].append({'id': 'A-BOOT-01', 'status': 'pass'})
            before = int(re.search(r'Foreground events: (\d+)', texts(tree)).group(1))
            foreground()
            wait_text(f'Foreground events: {before + 1}')
            tap_button(snapshot(), 'Detach listener')
            wait_text('Listener detached')
            foreground()
            tree = wait_text('Listener detached')
            after = int(re.search(r'Foreground events: (\d+)', texts(tree)).group(1))
            if after != before + 1:
                raise AssertionError('Detached listener received a foreground event.')
            capture('detached')
            result['checks'].append({'id': 'A-BOOT-02', 'status': 'pass', 'before': before, 'after': after})
        result['status'] = 'pass'
    except Exception as error:
        result['error'] = str(error)
        if serial:
            try:
                capture('failure')
            except Exception as capture_error:
                result['captureError'] = str(capture_error)
        raise
    finally:
        if recorder_pid and recorder_pid.isdigit():
            try:
                shell('kill', '-2', recorder_pid)
                time.sleep(2)
                command([*adb_command, '-s', serial, 'pull', f'/sdcard/lody-verify-{args.case}.mp4', args.output / f'{args.case}.mp4'], capture_output=True)
            except Exception as error:
                result['videoError'] = str(error)
                result['status'] = 'failed'
        if serial:
            with (args.output / 'logcat.txt').open('w') as file:
                subprocess.run([*adb_command, '-s', serial, 'logcat', '-d', '-t', '1500'], stdout=file, stderr=subprocess.STDOUT, timeout=20)
        (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        if emulator:
            if emulator.poll() is None:
                emulator.terminate()
            try:
                emulator.wait(timeout=20)
            except subprocess.TimeoutExpired:
                emulator.kill()
                emulator.wait(timeout=10)
        if emulator_log:
            emulator_log.close()
    if result['status'] != 'pass':
        raise RuntimeError('Required evidence was not captured.')
    print(args.output / 'result.json')


if __name__ == '__main__':
    main()
