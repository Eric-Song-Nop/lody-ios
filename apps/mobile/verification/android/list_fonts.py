"""Change Android font scale on the real, already-mounted grouped list."""
import re
import time


def run(shell, wait_text, tap_button, capture, texts, result, tree, appearance):
    original = shell('settings', 'get', 'system', 'font_scale').strip()
    result.update(appearance=appearance, originalFontScale=original)
    title = '这是一段需要自然换行的中文长标题，保持系统文字行为 Long text should wrap without clipping'

    def bounds(node):
        return tuple(map(int, re.findall(r'\d+', node.get('bounds'))))

    def measure(tree):
        label = next(node for node in tree.iter('node') if node.get('text') == title)
        row = next(node for node in tree.iter('node') if node.get('content-desc', '').startswith(title + ', '))
        label_bounds, row_bounds = bounds(label), bounds(row)
        if not (row_bounds[0] <= label_bounds[0] < label_bounds[2] <= row_bounds[2]
                and row_bounds[1] <= label_bounds[1] < label_bounds[3] <= row_bounds[3]):
            raise AssertionError('Long title extends beyond its native row')
        return label_bounds[3] - label_bounds[1], row_bounds

    def set_scale(scale):
        shell('settings', 'put', 'system', 'font_scale', scale)
        if float(shell('settings', 'get', 'system', 'font_scale')) != float(scale):
            raise AssertionError('System font scale did not change')

    try:
        set_scale('1.0')
        tap_button(wait_text('LodyKit: Android'), 'Open navigation verification')
        for host in ('page', 'sheet'):
            if host == 'sheet':
                tap_button(wait_text('Offline navigation: projects'), 'Settings')
            root = 'Offline navigation: projects' if host == 'page' else 'Offline navigation: settings'
            tap_button(wait_text(root), f'Open lists {host}')
            tree = wait_text(title)
            tap_button(tree, 'Count action, 0')
            tree = wait_text('Actions: 1; returns: 0; refreshes: 0')
            baseline_height, baseline_row = measure(tree)
            process = shell('pidof', 'app.innei.lody')
            capture(f'fonts-{host}-default')
            set_scale('1.3')
            deadline = time.monotonic() + 20
            while True:
                tree = wait_text(title)
                scaled_height, scaled_row = measure(tree)
                if scaled_height > baseline_height:
                    break
                if time.monotonic() >= deadline:
                    raise AssertionError('Mounted native title did not grow with system font scale')
                time.sleep(0.5)
            if 'Actions: 1; returns: 0; refreshes: 0' not in texts(tree):
                raise AssertionError('Font configuration change lost the active list state')
            if shell('pidof', 'app.innei.lody') != process:
                raise AssertionError('Font configuration restarted the application')
            capture(f'fonts-{host}-scaled')
            set_scale('1.0')
            deadline = time.monotonic() + 20
            while True:
                tree = wait_text(title)
                restored_height, _ = measure(tree)
                if restored_height == baseline_height:
                    break
                if time.monotonic() >= deadline:
                    raise AssertionError('Native text did not return to its original height')
                time.sleep(0.5)
            capture(f'fonts-{host}-restored')
            shell('input', 'keyevent', 'KEYCODE_BACK')
            tree = wait_text(root)
            if title in texts(tree):
                raise AssertionError('List host survived the system Back action')
            capture(f'fonts-{host}-closed')
            result['checks'].append({
                'id': f'A-UI-01-fonts-{host}', 'status': 'pass',
                'detail': 'Mounted native long title grows and restores with system font scale; counter/process retained and Back dismisses',
                'defaultTitleHeight': baseline_height, 'scaledTitleHeight': scaled_height,
                'defaultRowBounds': baseline_row, 'scaledRowBounds': scaled_row,
            })
    finally:
        if original == 'null':
            shell('settings', 'delete', 'system', 'font_scale')
        else:
            shell('settings', 'put', 'system', 'font_scale', original)
        actual = shell('settings', 'get', 'system', 'font_scale').strip()
        result['restoredFontScale'] = actual
        if actual != original:
            raise AssertionError(f'Failed to restore font scale: {actual!r} != {original!r}')
