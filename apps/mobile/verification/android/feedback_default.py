"""Capture the production toast before hierarchy collection can outlive it."""
import time


def run(shell, wait_text, tap_button, screenshot, capture, texts, result, tree, appearance, host):
    setting = 'accessibility_interactive_ui_timeout_ms'
    original = shell('settings', 'get', 'secure', setting)
    # A screen reader may legitimately extend the recommended timeout. Its
    # behavior belongs to the separate accessibility cases.
    enabled = shell('settings', 'get', 'secure', 'accessibility_enabled')
    if enabled not in ('0', 'null'):
        raise AssertionError('Default toast timing requires accessibility services disabled')
    result.update(feedbackHost=host, appearance=appearance,
                  originalInteractiveTimeout=original, interactiveTimeoutMs=0)
    try:
        shell('settings', 'put', 'secure', setting, '0')
        if shell('settings', 'get', 'secure', setting) != '0':
            raise AssertionError('Default accessibility timeout was not applied')
        tap_button(tree, 'Open navigation verification')
        if host == 'sheet':
            tap_button(wait_text('Offline navigation: projects'), 'Settings')
        root = 'Offline navigation: projects' if host == 'page' else 'Offline navigation: settings'
        tap_button(wait_text(root), f'Open feedback {host}')
        tree = wait_text('Native Android feedback')
        if f'Appearance: {appearance}; presses: 0' not in texts(tree):
            raise AssertionError('Wrong feedback fixture appearance or state')
        capture('default-toast-before')
        started = time.monotonic()
        tap_button(tree, 'Show info toast')
        if result.get('screenshotSource') == 'emulator':
            # Direct framebuffer reads can precede native rendering after adb
            # input returns. Take one scheduled sample, without retrying input
            # or extending the two-second capture deadline.
            time.sleep(max(0, 1 - (time.monotonic() - started)))
        # No UI Automator dump here: its idle wait can consume the entire toast.
        result['screenshotStartedSecondsAfterInput'] = time.monotonic() - started
        screenshot('default-toast-visible')
        captured = time.monotonic() - started
        result['visibleCaptureSecondsAfterInput'] = captured
        if captured > 2:
            raise AssertionError('Early toast screenshot missed the capture deadline')
        time.sleep(max(0, 6 - (time.monotonic() - started)))
        tree = wait_text('Native Android feedback')
        if 'Saved locally — 本机保存 100%' in texts(tree):
            raise AssertionError('Default toast remained after six seconds')
        result['expiryObservedSecondsAfterInput'] = time.monotonic() - started
        capture('default-toast-expired')
        shell('input', 'keyevent', 'KEYCODE_BACK')
        tree = wait_text(root)
        if 'Native Android feedback' in texts(tree):
            raise AssertionError('Feedback host remained after Back')
        capture('default-toast-closed')
        result['checks'].append({
            'id': f'A-UI-01-feedback-default-{host}', 'status': 'pass',
            'detail': 'Unextended system timeout, early screenshot, later toast absence and Back checked. Visual review must confirm the early screenshot actually shows the toast; this does not measure exact 3.2-second duration.',
        })
    finally:
        if original == 'null':
            shell('settings', 'delete', 'secure', setting)
        else:
            shell('settings', 'put', 'secure', setting, original)
        restored = shell('settings', 'get', 'secure', setting)
        result['restoredInteractiveTimeout'] = restored
        if restored != original:
            raise AssertionError('Accessibility timeout setting was not restored')
