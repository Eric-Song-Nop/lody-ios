"""Long labels, empty menus, live appearance and native keyboard focus."""
import re


def menu_button(tree):
    return next(node for node in tree.iter('node') if node.get('content-desc') == 'Edge menu')


def run(shell, wait_text, tap_button, capture, texts, result, tree, appearance):
    densities = re.findall(r'density:\s*(\d+)', shell('wm', 'density'), re.IGNORECASE)
    if not densities:
        raise AssertionError('Missing device density')
    density = int(densities[-1]) / 160
    result['appearance'] = appearance
    result['densityScale'] = density
    tap_button(tree, 'Open navigation verification')
    for host in ('page', 'sheet'):
        if host == 'page':
            tap_button(wait_text('Offline navigation: projects'), 'Open menu edges page')
        else:
            tap_button(wait_text('Offline navigation: projects'), 'Settings')
            tap_button(wait_text('Offline navigation: settings'), 'Open menu edges sheet')
        tree = wait_text('Native menu edge cases')
        button = menu_button(tree)
        x1, y1, x2, y2 = map(int, re.findall(r'\d+', button.attrib['bounds']))
        width, height = (x2-x1)/density, (y2-y1)/density
        if not (48 <= width <= 200.5 and height >= 48):
            raise AssertionError(f'Unexpected native menu bounds: {width} x {height} dp')
        result.setdefault('touchTargets', []).append({'host': host, 'widthDp': width, 'heightDp': height})
        capture(f'menu-edges-{host}-long-label')
        tap_button(tree, 'Disable menu')
        tree = wait_text('Selections: 0; menu: disabled')
        if menu_button(tree).get('enabled') != 'false':
            raise AssertionError('Empty native menu button is still enabled')
        tap_button(tree, 'Edge menu')
        tree = wait_text('Selections: 0; menu: disabled')
        if 'Enabled action' in texts(tree):
            raise AssertionError('Empty menu opened a popup')
        capture(f'menu-edges-{host}-disabled')
        tap_button(tree, 'Enable menu')
        tree = wait_text('Selections: 0; menu: enabled')
        tap_button(tree, 'Edge menu')
        wait_text('Enabled action')
        opposite = 'light' if appearance == 'dark' else 'dark'
        shell('cmd', 'uimode', 'night', 'yes' if opposite == 'dark' else 'no')
        tree = wait_text(f'Appearance: {opposite}')
        if 'Enabled action' in texts(tree):
            raise AssertionError('Menu survived configuration replacement')
        wait_text('Selections: 0; menu: enabled')
        tap_button(tree, 'Edge menu')
        tree = wait_text('Enabled action')
        capture(f'menu-edges-{host}-new-appearance')
        tap_button(tree, 'Enabled action')
        wait_text('Selections: 1; menu: enabled')
        shell('cmd', 'uimode', 'night', 'yes' if appearance == 'dark' else 'no')
        tree = wait_text(f'Appearance: {appearance}')
        for _ in range(12):
            if menu_button(tree).get('focused') == 'true':
                break
            shell('input', 'keyevent', 'KEYCODE_TAB')
            tree = wait_text('Native menu edge cases')
        else:
            raise AssertionError('Keyboard could not focus the native menu button')
        shell('input', 'keyevent', 'KEYCODE_ENTER')
        wait_text('Enabled action')
        capture(f'menu-edges-{host}-keyboard')
        shell('input', 'keyevent', 'KEYCODE_BACK')
        tree = wait_text('Selections: 1; menu: enabled')
        if menu_button(tree).get('focused') != 'true':
            raise AssertionError('Closing the menu lost native keyboard focus')
        capture(f'menu-edges-{host}-passed')
        shell('input', 'keyevent', 'KEYCODE_BACK')
        wait_text('Offline navigation: projects' if host == 'page' else 'Offline navigation: settings')
        result['checks'].append({'id': f'A-UI-01-menu-edges-{host}', 'status': 'pass', 'detail': '48 dp target, bounded long label, disabled empty menu, live appearance replacement and keyboard open/back focus restoration'})
