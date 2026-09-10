"""Use the installed TalkBack service and touch exploration, never a fake service."""
import re
import time

SERVICE = 'com.google.android.marvin.talkback/com.google.android.marvin.talkback.TalkBackService'


def run(shell, wait_text, tap_button, capture, texts, result, tree, appearance, host, target, snapshot):
    originals = {key: shell('settings', 'get', 'secure', key).strip()
                 for key in ('enabled_accessibility_services', 'accessibility_enabled')}
    result.update(appearance=appearance, host=host, target=target,
                  originalAccessibilitySettings=originals)
    headings = {'controls': 'Native Android controls', 'menus': 'Native Android menus',
                'lists': 'Native grouped rows'}
    tap_button(tree, 'Open navigation verification')
    root = 'Offline navigation: projects' if host == 'page' else 'Offline navigation: settings'
    if host == 'sheet':
        tap_button(wait_text('Offline navigation: projects'), 'Settings')
    tree = wait_text(root)
    entry_title = f'Open {target} {host}'
    # Only the internal fixture menu is searched this way, before enabling
    # TalkBack. Action assertions below still require the exact visible target.
    for attempt in range(6):
        if any(entry_title in (node.get('text'), node.get('content-desc'))
               for node in tree.iter('node')):
            tap_button(tree, entry_title)
            break
        capture(f'talkback-entry-search-{attempt}')
        if attempt == 5:
            raise AssertionError(f'Fixture entry not found after five scrolls: {entry_title}')
        containers = [node for node in tree.iter('node') if node.get('scrollable') == 'true']
        if len(containers) != 1:
            raise AssertionError('Fixture entry search requires one visible scroll container')
        left, top, right, bottom = map(int, re.findall(r'\d+', containers[0].get('bounds')))
        if right <= left or bottom <= top:
            raise AssertionError('Fixture scroll container has no visible bounds')
        x = str((left + right) // 2)
        start = str(top + (bottom - top) * 4 // 5)
        end = str(top + (bottom - top) // 5)
        result.setdefault('fixtureEntryScrolls', []).append({
            'title': entry_title, 'bounds': containers[0].get('bounds'),
            'from': [int(x), int(start)], 'to': [int(x), int(end)],
        })
        shell('input', 'touchscreen', 'swipe', x, start, x, end, '400')
        tree = snapshot()
    wait_text(headings[target])

    def wait_bound():
        deadline = time.monotonic() + 20
        while True:
            state = shell('dumpsys', 'accessibility')
            bound = re.search(r'Bound services:\{(.*?)\n\s*Enabled services:', state, re.S)
            if bound and 'TalkBackService' in bound.group(1) and 'touchExplorationEnabled=true' in state:
                return state
            if time.monotonic() >= deadline:
                raise AssertionError('Real TalkBack did not bind with touch exploration enabled')
            time.sleep(0.5)

    def activate(tree, title, hold=False):
        node = next(node for node in tree.iter('node')
                    if title in (node.get('text'), node.get('content-desc')))
        left, top, right, bottom = map(int, re.findall(r'\d+', node.get('bounds')))
        x, y = str((left + right) // 2), str((top + bottom) // 2)
        # A hierarchy dump may temporarily suppress other accessibility services.
        # Recheck after the dump; never count ordinary touch as a TalkBack action.
        before = wait_bound()
        # Explore this location first, then send a real touchscreen double tap.
        shell('input', 'touchscreen', 'swipe', x, y, x, y, '100')
        time.sleep(0.5)
        shell('input', 'tap', x, y)
        shell('input', 'touchscreen', 'swipe', x, y, x, y, '800' if hold else '60')
        after = wait_bound()
        result.setdefault('talkBackInputs', []).append({
            'title': title, 'bounds': node.get('bounds'),
            'gesture': 'explore then double-tap-and-hold' if hold else 'explore then double-tap',
            'accessibilityBefore': before, 'accessibilityAfter': after,
        })

    try:
        existing = originals['enabled_accessibility_services']
        services = [] if existing in ('null', '') else existing.split(':')
        if SERVICE not in services:
            services.append(SERVICE)
        shell('settings', 'put', 'secure', 'enabled_accessibility_services', ':'.join(services))
        shell('settings', 'put', 'secure', 'accessibility_enabled', '1')
        result['activeAccessibilityState'] = wait_bound()
        result['talkBackPackage'] = shell('dumpsys', 'package', 'com.google.android.marvin.talkback')
        capture('talkback-enabled')
        tree = wait_text(headings[target])
        if target == 'controls':
            activate(tree, 'Increment native counter')
            tree = wait_text('Icon presses: 1; long presses: 0')
            capture('talkback-icon-activated')
            activate(tree, 'Native text action')
            tree = wait_text('Text presses: 1; disabled presses: 0')
            disabled = next(node for node in tree.iter('node') if node.get('content-desc') == 'Disabled native counter')
            if disabled.get('enabled') != 'false':
                raise AssertionError('Disabled native control is exposed as enabled')
        elif target == 'menus':
            activate(tree, 'Choose item filter')
            tree = wait_text('Recent items')
            capture('talkback-menu-open')
            activate(tree, 'Recent items')
            tree = wait_text('Selected: recent; selections: 1')
            activate(tree, 'Context item', hold=True)
            tree = wait_text('Remove item')
            capture('talkback-context-open')
            activate(tree, 'Remove item')
            tree = wait_text('Action: remove; actions: 1; child presses: 0')
        else:
            activate(tree, 'Count action, 0')
            tree = wait_text('Actions: 1; returns: 0; refreshes: 0')
            capture('talkback-row-activated')
            activate(tree, 'Open list detail, 原生导航行 · Native navigation')
            wait_text('Native list detail')
            capture('talkback-detail-open')
            shell('input', 'keyevent', 'KEYCODE_BACK')
            tree = wait_text('Actions: 1; returns: 1; refreshes: 0')
        capture('talkback-actions-passed')
        shell('input', 'keyevent', 'KEYCODE_BACK')
        tree = wait_text(root)
        if headings[target] in texts(tree):
            raise AssertionError('TalkBack host remained open after Back')
        capture('talkback-returned')
        result['checks'].append({
            'id': f'A-UI-01-talkback-{target}-{host}', 'status': 'pass',
            'detail': 'Real bound TalkBack with touch exploration activates native controls through touchscreen gestures; action counts and Back result checked. No speech-quality claim.',
        })
    except Exception:
        capture('talkback-before-restoration-failure')
        raise
    finally:
        for key, value in originals.items():
            if value == 'null':
                shell('settings', 'delete', 'secure', key)
            else:
                shell('settings', 'put', 'secure', key, value)
        restored = {key: shell('settings', 'get', 'secure', key).strip() for key in originals}
        result['restoredAccessibilitySettings'] = restored
        if restored != originals:
            raise AssertionError(f'Failed to restore accessibility settings: {restored}')
