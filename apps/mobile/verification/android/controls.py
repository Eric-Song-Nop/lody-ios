"""Drive real LodyKit controls in the page and sheet hosts."""
import re


def run(shell, wait_text, tap_button, capture, texts, result, tree, appearance):
    densities = re.findall(r'density:\s*(\d+)', shell('wm', 'density'), re.IGNORECASE)
    if not densities:
        raise AssertionError('Missing device density for touch-target verification')
    density = int(densities[-1]) / 160
    result['densityScale'] = density
    result['appearance'] = appearance
    tap_button(tree, 'Open navigation verification')
    for host in ('page', 'sheet'):
        if host == 'page':
            tap_button(wait_text('Offline navigation: projects'), 'Open controls page')
        else:
            tap_button(wait_text('Offline navigation: projects'), 'Settings')
            tap_button(wait_text('Offline navigation: settings'), 'Open controls sheet')
        tree = wait_text('Native Android controls')
        if f'Appearance: {appearance}' not in texts(tree):
            raise AssertionError('Controls did not follow the requested system appearance')
        button = next(node for node in tree.iter('node') if node.get('content-desc') == 'Increment native counter')
        x1, y1, x2, y2 = map(int, re.findall(r'\d+', button.attrib['bounds']))
        if min(x2 - x1, y2 - y1) / density < 48:
            raise AssertionError(f'Icon target below 48 dp: {button.attrib["bounds"]}')
        result.setdefault('touchTargets', []).append({'host': host, 'bounds': button.attrib['bounds'], 'minimumDp': min(x2-x1, y2-y1)/density})
        tap_button(tree, 'Increment native counter')
        wait_text('Icon presses: 1; long presses: 0')
        x, y = str((x1 + x2) // 2), str((y1 + y2) // 2)
        shell('input', 'touchscreen', 'swipe', x, y, x, y, '800')
        tree = wait_text('Icon presses: 1; long presses: 1')
        tap_button(tree, 'Disabled native counter')
        tap_button(wait_text('disabled presses: 0'), 'Native text action')
        tree = wait_text('Text presses: 1; disabled presses: 0')
        tap_button(tree, 'Disabled text action')
        wait_text('Text presses: 1; disabled presses: 0')
        capture(f'controls-{host}-passed')
        opposite = 'light' if appearance == 'dark' else 'dark'
        shell('cmd', 'uimode', 'night', 'yes' if opposite == 'dark' else 'no')
        wait_text(f'Appearance: {opposite}')
        wait_text('Text presses: 1; disabled presses: 0')
        capture(f'controls-{host}-appearance-changed')
        shell('cmd', 'uimode', 'night', 'yes' if appearance == 'dark' else 'no')
        wait_text(f'Appearance: {appearance}')
        shell('input', 'keyevent', 'KEYCODE_BACK')
        expected = 'Offline navigation: projects' if host == 'page' else 'Offline navigation: settings'
        wait_text(expected)
        result['checks'].append({'id': f'A-UI-01-controls-{host}', 'status': 'pass', 'detail': 'Native click/long-click, disabled actions, shared text button, system appearance and 48 dp icon target'})
