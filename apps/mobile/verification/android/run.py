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
import gesture
import hardware_touch
import accessibility_observer
import controls
import symbols
import menus
import menu_edges
import lists
import list_fonts
import list_focus
import talkback
import list_mutations
import locales
import locale_switch
import system_api
import feedback
import feedback_default
import feedback_keyboard
import png_capture

ROOT = Path(__file__).resolve().parents[4]
SDK = Path(os.environ.get('ANDROID_HOME', Path.home() / 'Library/Android/sdk'))
PACKAGE = 'app.innei.lody'


def command(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, timeout=kwargs.pop('timeout', 60), **kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--case', choices=['bootstrap', 'wasm', 'recovery', 'storage', 'navigation', 'navigation-interruption', 'navigation-teardown', 'controls', 'symbols', 'menus', 'menu-edges', 'lists', 'list-fonts', 'list-focus', 'talkback', 'list-mutations', 'locales', 'locale-switch', 'system', 'feedback', 'feedback-default', 'feedback-keyboard'], required=True)
    parser.add_argument('--appearance', choices=['light', 'dark'], default='light', help='System appearance for control/menu cases; restored after verification.')
    parser.add_argument('--talkback-host', choices=['page', 'sheet'], default='page')
    parser.add_argument('--talkback-target', choices=['controls', 'menus', 'lists'], default='controls')
    parser.add_argument('--talkback-traversal', action='store_true', help='Verify native control order through real TalkBack next/previous gestures.')
    parser.add_argument('--record-input-events', action='store_true', help='Record device getevent timestamps for owned-emulator TalkBack input diagnosis.')
    parser.add_argument('--list-return', choices=['present', 'removed', 'disabled'], default='present', help='Source navigation row state while detail is open; list-focus or TalkBack lists only.')
    parser.add_argument('--symbols-host', choices=['page', 'sheet'], default='page', help='Review one native symbol host per recording.')
    parser.add_argument('--locale-host', choices=['page', 'sheet'], default='page', help='Host for real application language switching.')
    parser.add_argument('--feedback-host', choices=['page', 'sheet'], default='page', help='Feedback host; run both separately to keep each recording within 180 seconds.')
    parser.add_argument('--screenshot-source', choices=['adb', 'emulator'], default='adb', help='Explicit default-toast capture transport; emulator requires a runner-owned AVD and gRPC dependencies.')
    parser.add_argument('--adb-port', type=int, default=5038, help='Dedicated SDK adb server; leaves the default 5037 server alone.')
    parser.add_argument('--serial', help='Caller-owned device; installs and clears only app.innei.lody.')
    parser.add_argument('--avd', default='Lody_Android_Verify_36')
    parser.add_argument('--settle-seconds', type=int, default=0, help='Optional device boot settling time before app installation and recording.')
    parser.add_argument('--gpu', choices=['auto', 'host', 'software'], default='host')
    parser.add_argument('--memory-mb', type=int, default=4096, help='RAM for the owned emulator; does not modify its saved AVD configuration.')
    parser.add_argument('--avd-home', type=Path, help='AVD registry directory when SDK tools use a different default.')
    parser.add_argument('--output', type=Path, default=ROOT / '.artifacts/android' / time.strftime('%Y%m%d-%H%M%S'))
    args = parser.parse_args()
    if args.record_input_events and args.case != 'talkback':
        parser.error('--record-input-events requires talkback.')
    if args.list_return != 'present' and not (args.case == 'list-focus' or (args.case == 'talkback' and args.talkback_target == 'lists')):
        parser.error('--list-return requires list-focus or talkback lists.')
    if args.talkback_traversal and (args.case != 'talkback' or args.talkback_target != 'controls'):
        parser.error('--talkback-traversal currently requires talkback controls.')
    if args.screenshot_source == 'emulator' and (args.serial or args.case != 'feedback-default'):
        parser.error('Emulator screenshots require feedback-default on a runner-owned AVD.')
    if not 0 <= args.settle_seconds <= 180:
        parser.error('--settle-seconds must be between 0 and 180.')
    if args.memory_mb < 2048:
        parser.error('--memory-mb must be at least 2048.')
    if not args.apk.is_file():
        parser.error('APK does not exist; run pnpm build:android first.')
    args.output.mkdir(parents=True, exist_ok=False)
    adb = SDK / 'platform-tools/adb'
    adb_command = [str(adb), '-P', str(args.adb_port)]
    emulator = None
    emulator_log = None
    logcat_process = None
    logcat_file = None
    input_process = None
    input_file = None
    recorder_pid = None
    original_night_mode = None
    observer_remote = None
    observer = None
    original_accessibility_settings = None
    serial = args.serial
    touch_driver = None
    result = {'apkSha256': hashlib.file_digest(args.apk.open('rb'), 'sha256').hexdigest(), 'case': args.case, 'status': 'failed', 'checks': [], 'commit': command(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()}
    result['workingTreeDirty'] = bool(command(['git', 'status', '--porcelain'], cwd=ROOT, capture_output=True, text=True).stdout.strip())
    result['fixtureVersion'] = 'bootstrap-v1'

    def shell(*parts):
        return command([*adb_command, '-s', serial, 'shell', *parts], capture_output=True, text=True).stdout.strip()

    def snapshot():
        if observer:
            return observer.snapshot()
        if observer_remote:
            raise RuntimeError('TalkBack observer did not initialize; suppressing fallback forbidden')
        shell('uiautomator', 'dump', '/sdcard/lody-verify.xml')
        xml = shell('cat', '/sdcard/lody-verify.xml')
        return ET.fromstring(xml)

    def texts(tree):
        return '\n'.join(node.get('text', '') for node in tree.iter('node'))

    def wait_text(expected, timeout=30):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            tree = snapshot()
            if 'WASM failed:' in texts(tree) or 'Recovery failed:' in texts(tree) or 'Storage failed:' in texts(tree):
                raise AssertionError(texts(tree))
            if expected in texts(tree):
                return tree
            time.sleep(0.5)
        raise AssertionError(f'Missing UI state: {expected}')

    def screenshot(name):
        if args.case == 'feedback-default':
            if args.screenshot_source == 'emulator':
                timing = touch_driver.screenshot(args.output / f'{name}.png')
            else:
                timing = png_capture.capture([*adb_command, '-s', serial, 'exec-out', 'screencap', '-p'],
                                             args.output / f'{name}.png')
            result.setdefault('screenshotTimings', {})[name] = timing
            return timing
        with (args.output / f'{name}.png').open('wb') as file:
            command([*adb_command, '-s', serial, 'exec-out', 'screencap', '-p'], stdout=file)

    def capture(name):
        screenshot(name)
        (args.output / f'{name}.xml').write_text(ET.tostring(snapshot(), encoding='unicode'))

    def foreground():
        shell('input', 'keyevent', 'KEYCODE_HOME')
        time.sleep(1)
        shell('am', 'start', '-W', '-n', f'{PACKAGE}/.MainActivity')

    def tap_button(tree, title):
        button = next(node for node in tree.iter('node') if title.lower() in (node.get('text', '').lower(), node.get('content-desc', '').lower()))
        x1, y1, x2, y2 = map(int, re.findall(r'\d+', button.attrib['bounds']))
        x, y = str((x1 + x2) // 2), str((y1 + y2) // 2)
        result.setdefault('inputs', []).append({'title': title, 'bounds': button.attrib['bounds'], 'durationMs': 100})
        shell('input', 'touchscreen', 'swipe', x, y, x, y, '100')

    try:
        if args.case == 'talkback' and serial:
            raise RuntimeError('TalkBack hardware verification requires a runner-owned emulator')
        use_emulator_rpc = args.case == 'talkback' or args.screenshot_source == 'emulator'
        touch_prepared = hardware_touch.prepare(SDK, args.output) if use_emulator_rpc else None
        gesture_dex = gesture.build(SDK, args.output) if args.case == 'navigation-interruption' else None
        talkback_dex = gesture.build(SDK, args.output, 'AccessibilityDump') if args.case == 'talkback' else None
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
            grpc_args = []
            if touch_prepared:
                with socket.socket() as probe:
                    probe.bind(('127.0.0.1', 0))
                    grpc_port = probe.getsockname()[1]
                grpc_args = ['-grpc', str(grpc_port), '-grpc-use-token']
            emulator = subprocess.Popen([str(SDK / 'emulator/emulator'), '-avd', args.avd, '-port', str(port), '-no-snapshot', '-gpu', args.gpu, '-memory', str(args.memory_mb), '-no-boot-anim', '-no-audio', *grpc_args], stdout=emulator_log, stderr=subprocess.STDOUT, env=emulator_env)
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
        if touch_prepared:
            touch_driver = hardware_touch.connect(touch_prepared, emulator.pid, grpc_port)
        result['bootSettleSeconds'] = args.settle_seconds
        if args.settle_seconds:
            time.sleep(args.settle_seconds)
        result['serial'] = serial
        result['system'] = shell('getprop', 'ro.build.fingerprint')
        result['abi'] = shell('getprop', 'ro.product.cpu.abi')
        if args.case in ('controls', 'symbols', 'menus', 'menu-edges', 'lists', 'list-fonts', 'list-focus', 'talkback', 'list-mutations', 'locales', 'locale-switch', 'system', 'feedback', 'feedback-default', 'feedback-keyboard'):
            mode = shell('cmd', 'uimode', 'night')
            match = re.search(r'\b(auto|yes|no|custom)\b', mode)
            if not match:
                raise RuntimeError(f'Cannot preserve system night mode: {mode}')
            original_night_mode = match.group(1)
            shell('cmd', 'uimode', 'night', 'yes' if args.appearance == 'dark' else 'no')
        command([*adb_command, '-s', serial, 'install', '-r', args.apk], capture_output=True, text=True)
        shell('pm', 'clear', PACKAGE)
        shell('input', 'keyevent', 'KEYCODE_WAKEUP')
        shell('wm', 'dismiss-keyguard')
        if talkback_dex:
            # UiAutomation itself affects accessibility_enabled. Preserve the
            # device state before registering even a non-suppressing observer.
            original_accessibility_settings = {
                key: shell('settings', 'get', 'secure', key).strip()
                for key in ('enabled_accessibility_services', 'accessibility_enabled')}
            result['originalAccessibilitySettings'] = original_accessibility_settings
            observer_remote = '/data/local/tmp/lody-verify-observer.dex'
            command([*adb_command, '-s', serial, 'push', talkback_dex, observer_remote], capture_output=True)
            observer = accessibility_observer.Observer(adb_command, serial, observer_remote, args.output)
            result['hierarchyObserver'] = 'persistent UiAutomation.FLAG_DONT_SUPPRESS_ACCESSIBILITY_SERVICES'
            result['observerDexSha256'] = hashlib.file_digest(talkback_dex.open('rb'), 'sha256').hexdigest()
        logcat_file = (args.output / 'logcat.txt').open('w')
        logcat_process = subprocess.Popen([*adb_command, '-s', serial, 'logcat', '-v', 'threadtime', '-T', '1'], stdout=logcat_file, stderr=subprocess.STDOUT)
        if args.record_input_events:
            input_file = (args.output / 'input-events.txt').open('w')
            input_process = subprocess.Popen([*adb_command, '-s', serial, 'shell', 'getevent', '-lt'], stdout=input_file, stderr=subprocess.STDOUT)
            result['inputEventRecording'] = 'getevent -lt; device monotonic timestamps'
        recorder_pid = shell('sh', '-c', f"'screenrecord --time-limit 180 /sdcard/lody-verify-{args.case}.mp4 >/dev/null 2>&1 & echo $!'")
        if not recorder_pid.isdigit():
            raise RuntimeError(f'Could not start screenrecord: {recorder_pid}')
        shell('am', 'start', '-W', '-n', f'{PACKAGE}/.MainActivity')
        tree = wait_text('LodyKit: Android')
        capture('boot')
        if args.case == 'controls':
            result['fixtureVersion'] = 'controls-v1'
            controls.run(shell, wait_text, tap_button, capture, texts, result, tree, args.appearance)
        elif args.case == 'menus':
            result['fixtureVersion'] = 'menus-v1'
            menus.run(shell, wait_text, tap_button, capture, texts, result, tree, args.appearance)
        elif args.case == 'feedback':
            result['fixtureVersion'] = 'feedback-v3'
            feedback.run(shell, wait_text, tap_button, capture, texts, result, tree, args.appearance, args.feedback_host)
        elif args.case == 'feedback-default':
            result['fixtureVersion'] = 'feedback-default-v4'
            result['screenshotSource'] = args.screenshot_source
            feedback_default.run(shell, wait_text, tap_button, screenshot, capture, texts, result, tree, args.appearance, args.feedback_host)
        elif args.case == 'feedback-keyboard':
            result['fixtureVersion'] = 'feedback-keyboard-v2'
            feedback_keyboard.run(shell, wait_text, tap_button, capture, texts, result, tree, args.appearance, args.feedback_host)
        elif args.case == 'system':
            result['fixtureVersion'] = 'system-v1'
            system_api.run(shell, wait_text, tap_button, capture, texts, result, tree, args.appearance)
        elif args.case == 'locale-switch':
            result['fixtureVersion'] = 'locale-switch-v5'
            locale_switch.run(shell, wait_text, tap_button, capture, texts, result, tree, args.appearance, args.locale_host)
        elif args.case == 'locales':
            result['fixtureVersion'] = 'locales-v1'
            locales.run(shell, wait_text, tap_button, capture, texts, result, tree, args.appearance)
        elif args.case == 'list-mutations':
            result['fixtureVersion'] = 'list-mutations-v1'
            list_mutations.run(shell, wait_text, tap_button, capture, texts, result, tree, args.appearance)
        elif args.case == 'talkback':
            result['fixtureVersion'] = 'talkback-v7' if args.talkback_target == 'lists' else 'talkback-v5'
            talkback.run(shell, wait_text, tap_button, capture, texts, result, tree, args.appearance, args.talkback_host, args.talkback_target, snapshot,
                         touch_driver.run, args.talkback_traversal, args.list_return)
        elif args.case == 'symbols':
            result['fixtureVersion'] = 'symbols-v1'
            symbols.run(shell, wait_text, tap_button, capture, texts, result, tree, args.appearance, args.symbols_host)
        elif args.case == 'list-focus':
            result['fixtureVersion'] = 'list-focus-v2'
            list_focus.run(shell, wait_text, tap_button, capture, texts, result, tree, args.appearance, args.list_return)
        elif args.case == 'list-fonts':
            result['fixtureVersion'] = 'list-fonts-v1'
            list_fonts.run(shell, wait_text, tap_button, capture, texts, result, tree, args.appearance)
        elif args.case == 'lists':
            result['fixtureVersion'] = 'lists-v2'
            lists.run(shell, wait_text, tap_button, capture, texts, result, tree, args.appearance)
        elif args.case == 'menu-edges':
            result['fixtureVersion'] = 'menu-edges-v1'
            menu_edges.run(shell, wait_text, tap_button, capture, texts, result, tree, args.appearance)
        elif args.case == 'navigation-teardown':
            result['fixtureVersion'] = 'navigation-teardown-v1'
            for cycle in range(1, 3):
                tap_button(tree, 'Open navigation verification')
                tap_button(wait_text('Offline navigation: projects'), 'Settings')
                tap_button(wait_text('Offline navigation: settings'), 'Open form sheet')
                tap_button(wait_text('Offline navigation: sheet'), 'Push sheet child')
                tree = wait_text('Offline navigation: sheet child')
                capture(f'teardown-nested-{cycle}')
                tap_button(tree, 'Dismiss entire navigation')
                tree = wait_text('Navigation audit: mounted=0 pending=0 retained=0 observed=1 settled=2 cancelled=2')
                capture(f'teardown-released-{cycle}')
            result['checks'].append({'id': 'A-NAV-03-teardown', 'status': 'pass', 'detail': 'Two complete host dismissals release mounted pages, both pending results and the observed presentation session'})
        elif args.case == 'navigation-interruption':
            result['fixtureVersion'] = 'navigation-interruption-v4'
            result['gestureDriverSha256'] = hashlib.file_digest(gesture_dex.open('rb'), 'sha256').hexdigest()
            mode = shell('settings', 'get', 'secure', 'navigation_mode')
            if mode != '2':
                raise AssertionError(f'Gesture navigation is required for interruption evidence; actual mode={mode}')
            tap_button(tree, 'Open navigation verification')
            tap_button(wait_text('Offline navigation: projects'), 'Open offline project')
            tree = wait_text('Offline navigation: sessions')
            bounds = list(map(int, re.findall(r'\d+', next(tree.iter('node')).attrib['bounds'])))
            width, height = bounds[2], bounds[3]
            y = str(height // 2)
            gesture.cancel(adb_command, serial, gesture_dex, args.output, width, height, screenshot)
            wait_text('Offline navigation: sessions')
            capture('back-gesture-cancelled')
            shell('input', 'touchscreen', 'swipe', '1', y, str(width // 2), y, '300')
            tree = wait_text('Project returns: 1')
            for count in range(2, 5):
                tap_button(tree, 'Open offline project')
                shell('input', 'keyevent', 'KEYCODE_BACK')
                tree = wait_text(f'Project returns: {count}')
            tap_button(tree, 'Open offline project')
            tap_button(wait_text('Offline navigation: sessions'), 'Settings')
            tap_button(wait_text('Offline navigation: settings'), 'Projects')
            wait_text('Offline navigation: sessions')
            shell('input', 'keyevent', 'KEYCODE_BACK')
            tree = wait_text('Project returns: 5')
            capture('navigation-interruption-passed')
            tap_button(tree, 'Return to runtime verification')
            tree = wait_text('Navigation audit: mounted=0 pending=0 retained=0')
            if 'settled=5 cancelled=5' not in texts(tree):
                raise AssertionError('Rapid return did not release all five presentation results')
            capture('rapid-return-released')
            result['checks'].append({'id': 'A-NAV-03-rapid-return', 'status': 'pass', 'detail': 'Committed edge gesture, three immediate returns, retained tab stacks and all five presentation results released'})
            result['visualReviewRequired'] = ['Confirm the system recognized the held edge gesture in back-gesture-preview.png/video, then retained Sessions after cancellation. This is not a claim of a page-level predictive transition animation.']
        elif args.case == 'navigation':
            result['fixtureVersion'] = 'navigation-v3'
            tap_button(tree, 'Open navigation verification')
            tap_button(wait_text('Offline navigation: projects'), 'Open offline project')
            tap_button(wait_text('Offline navigation: sessions'), 'Open offline session')
            wait_text('Offline navigation: messages')
            capture('messages')
            shell('input', 'keyevent', 'KEYCODE_BACK')
            wait_text('Offline navigation: sessions')
            shell('input', 'keyevent', 'KEYCODE_BACK')
            tree = wait_text('Project returns: 1')
            result['checks'].append({'id': 'A-NAV-01', 'status': 'pass'})
            tap_button(tree, 'Settings')
            tap_button(wait_text('Offline navigation: settings'), 'Open form sheet')
            tap_button(wait_text('Offline navigation: sheet'), 'Complete sheet')
            tree = wait_text('Settled sheets: 1')
            if 'Sheet result: completed' not in texts(tree):
                raise AssertionError('Sheet completion result was lost')
            tap_button(tree, 'Open page sheet')
            wait_text('Offline navigation: sheet')
            shell('input', 'keyevent', 'KEYCODE_BACK')
            tree = wait_text('Settled sheets: 2')
            if 'Sheet result: cancelled' not in texts(tree):
                raise AssertionError('System back did not cancel the sheet')
            tap_button(tree, 'Open form sheet')
            tap_button(wait_text('Offline navigation: sheet'), 'Push sheet child')
            wait_text('Offline navigation: sheet child')
            shell('input', 'keyevent', 'KEYCODE_BACK')
            tree = wait_text('Child result: cancelled')
            capture('nested-return')
            tap_button(tree, 'Close Navigation sheet')
            tree = wait_text('Settled sheets: 3')
            if 'Sheet result: cancelled' not in texts(tree):
                raise AssertionError('Native close did not settle cancellation')
            tap_button(tree, 'Open form sheet')
            tap_button(wait_text('Offline navigation: sheet'), 'Cancel sheet')
            tree = wait_text('Settled sheets: 4')
            if 'Sheet result: cancelled' not in texts(tree):
                raise AssertionError('Explicit cancellation result was lost')
            tap_button(tree, 'Open form sheet')
            tap_button(wait_text('Offline navigation: sheet'), 'Push sheet child')
            tap_button(wait_text('Offline navigation: sheet child'), 'Complete child')
            tree = wait_text('Child result: completed')
            capture('nested-completed')
            header = next(node for node in tree.iter('node') if node.get('text') == 'Navigation sheet')
            x1, y1, x2, y2 = map(int, re.findall(r'\d+', header.attrib['bounds']))
            _, _, _, height = map(int, re.findall(r'\d+', next(tree.iter('node')).attrib['bounds']))
            shell('input', 'touchscreen', 'swipe', str((x1 + x2) // 2), str((y1 + y2) // 2), str((x1 + x2) // 2), str(height - 50), '350')
            tree = wait_text('Settled sheets: 5')
            if 'Sheet result: cancelled' not in texts(tree):
                raise AssertionError('Downward sheet dismissal did not settle cancellation')
            tap_button(tree, 'Open form sheet')
            tap_button(wait_text('Offline navigation: sheet'), 'Push sheet child')
            tap_button(wait_text('Offline navigation: sheet child'), 'Navigate up')
            tree = wait_text('Child result: cancelled')
            capture('toolbar-nested-return')
            tap_button(tree, 'Navigate up')
            tree = wait_text('Settled sheets: 6')
            if 'Sheet result: cancelled' not in texts(tree):
                raise AssertionError('Sheet toolbar return did not settle cancellation')
            result['checks'].append({'id': 'A-NAV-02', 'status': 'pass'})
            result['checks'].append({'id': 'A-NAV-03-nested-return', 'status': 'pass', 'detail': 'Nested system/toolbar return and completion retain their parent; all six outer results settle once'})
            capture('navigation-passed')
        elif args.case == 'storage':
            tap_button(tree, 'Run storage verification')
            wait_text('Storage prepared: restart required', timeout=180)
            capture('prepared')
            command([*adb_command, '-s', serial, 'pull', f'/sdcard/Android/data/{PACKAGE}/files/lody-runtime-verification.json', args.output / 'seed-runtime.json'], capture_output=True)
            seed = json.loads((args.output / 'seed-runtime.json').read_text())
            required_seed = {'increment', 'compressed', 'large', 'output-limit', 'truncated-length', 'truncated-body', 'invalid-json', 'over-limit'}
            if {case['name'] for case in seed['cases'] if case['status'] == 'pass'} != required_seed or not seed.get('verifiedCatalog'):
                raise AssertionError('Storage seed did not come from the verified real WASM pipeline')
            result['seedRuntimeSha256'] = seed['runtimeSha256']
            shell('am', 'force-stop', PACKAGE)
            shell('am', 'start', '-W', '-n', f'{PACKAGE}/.MainActivity')
            tree = wait_text('Storage not run')
            tap_button(tree, 'Run storage verification')
            wait_text('Storage passed:', timeout=60)
            command([*adb_command, '-s', serial, 'pull', f'/sdcard/Android/data/{PACKAGE}/files/lody-storage-verification.json', args.output / 'storage.json'], capture_output=True)
            storage = json.loads((args.output / 'storage.json').read_text())
            actual = {case['id'] for case in storage['cases'] if case['status'] == 'pass'}
            if actual != {f'A-STORE-{number:02d}' for number in range(1, 5)}:
                raise AssertionError(f'Storage coverage mismatch: {actual}')
            if storage['processId'] == storage['priorProcessId'] or storage['projectionUtf8Bytes'] < 2 * 1024 * 1024 or storage.get('runtimeSeeded') is not True:
                raise AssertionError('Storage did not cover real process restart and large projection')
            for boundary in ('restoredEnvelopeRejected', 'tamperedEnvelopeRejected', 'backupDisabled', 'corruptDatabaseRecovered'):
                if storage.get(boundary) is not True:
                    raise AssertionError(f'Storage boundary was not verified: {boundary}')
            result['fixtureVersion'] = storage['fixtureVersion']
            result['checks'] = storage['cases']
            capture('storage-passed')
        elif args.case == 'recovery':
            result['webViewProvider'] = shell('dumpsys', 'webviewupdate')
            tap_button(tree, 'Run recovery verification')
            wait_text('Recovery background ready', timeout=90)
            capture('before-background')
            shell('input', 'keyevent', 'KEYCODE_HOME')
            time.sleep(3)
            shell('am', 'start', '-W', '-n', f'{PACKAGE}/.MainActivity')
            wait_text('Recovery passed:', timeout=150)
            command([*adb_command, '-s', serial, 'pull', f'/sdcard/Android/data/{PACKAGE}/files/lody-recovery-verification.json', args.output / 'runtime.json'], capture_output=True)
            runtime = json.loads((args.output / 'runtime.json').read_text())
            actual = {case['id'] for case in runtime['cases'] if case['status'] == 'pass'}
            if actual != {f'A-REC-{number:02d}' for number in range(1, 6)}:
                raise AssertionError(f'Recovery coverage mismatch: {actual}')
            if runtime['httpWrites'] != 0 or runtime['createdViews'] != runtime['closedViews']:
                raise AssertionError('Recovery leaked an owner or performed a write')
            result['fixtureVersion'] = runtime['fixtureVersion']
            result['checks'] = runtime['cases']
            capture('recovery-passed')
        elif args.case == 'wasm':
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
        result['error'] = f'{type(error).__name__}: {error}'
        if isinstance(error, subprocess.CalledProcessError):
            stderr = error.stderr
            result['commandStderr'] = stderr.decode('utf-8', errors='replace') if isinstance(stderr, bytes) else stderr
        if serial:
            try:
                capture('failure')
            except Exception as capture_error:
                result['captureError'] = str(capture_error)
        raise
    finally:
        if input_process:
            if input_process.poll() is not None:
                result['inputEventRecordingError'] = f'getevent exited early: {input_process.returncode}'
                result['status'] = 'failed'
            else:
                input_process.terminate()
            try:
                input_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                input_process.kill()
                input_process.wait(timeout=5)
            input_file.close()
        if observer:
            try:
                observer.save_events()
            except Exception as error:
                result['observerEventsError'] = str(error)
                result['status'] = 'failed'
            try:
                observer.close()
                result['observerClosed'] = True
                result['observerRequests'] = observer.requests
            except Exception as error:
                result['observerCloseError'] = str(error)
                result['status'] = 'failed'
        if original_accessibility_settings is not None:
            try:
                for key, value in original_accessibility_settings.items():
                    if value == 'null':
                        shell('settings', 'delete', 'secure', key)
                    else:
                        shell('settings', 'put', 'secure', key, value)
                restored = {key: shell('settings', 'get', 'secure', key).strip()
                            for key in original_accessibility_settings}
                result['restoredAccessibilitySettings'] = restored
                if restored != original_accessibility_settings:
                    raise AssertionError(f'Failed to restore accessibility settings: {restored}')
            except Exception as error:
                result['accessibilityRestoreError'] = str(error)
                result['status'] = 'failed'
        if observer_remote:
            try:
                shell('rm', '-f', observer_remote)
            except Exception as error:
                result['observerCleanupError'] = str(error)
                result['status'] = 'failed'
        if recorder_pid and recorder_pid.isdigit():
            try:
                shell('kill', '-2', recorder_pid)
                time.sleep(2)
            except Exception as error:
                result['videoError'] = str(error)
                result['status'] = 'failed'
            try:
                # Keep partial video even if screenrecord already hit its time limit.
                command([*adb_command, '-s', serial, 'pull', f'/sdcard/lody-verify-{args.case}.mp4', args.output / f'{args.case}.mp4'], capture_output=True)
            except Exception as error:
                result['videoPullError'] = str(error)
                result['status'] = 'failed'
        if original_night_mode is not None:
            try:
                shell('cmd', 'uimode', 'night', original_night_mode)
                result['nightModeRestored'] = original_night_mode
            except Exception as error:
                result['nightModeRestoreError'] = str(error)
                result['status'] = 'failed'
        if logcat_process:
            logcat_process.terminate()
            try:
                logcat_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logcat_process.kill()
                logcat_process.wait(timeout=5)
            logcat_file.close()
        elif serial:
            with (args.output / 'logcat.txt').open('w') as file:
                subprocess.run([*adb_command, '-s', serial, 'logcat', '-d', '-t', '1500'], stdout=file, stderr=subprocess.STDOUT, timeout=20)
        (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        if touch_driver:
            touch_driver.close()
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
