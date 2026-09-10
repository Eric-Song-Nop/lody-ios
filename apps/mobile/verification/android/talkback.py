"""Use the installed TalkBack service and touch exploration, never a fake service."""
import re
import time

SERVICE = 'com.google.android.marvin.talkback/com.google.android.marvin.talkback.TalkBackService'


def run(shell, wait_text, tap_button, capture, texts, result, tree, appearance, host, target, snapshot, gesture_input):
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
            result['lastObservedAccessibilityState'] = state
            bound = re.search(r'Bound services:\{(.*?)\n\s*Enabled services:', state, re.S)
            enabled = re.search(r'Enabled services:\{([^\n]*)', state)
            # Android dumps a service label in the bound section, not its class.
            # Require the real component in Enabled as well as the bound label.
            if (bound and 'Service[label=TalkBack,' in bound.group(1)
                    and enabled and any(component in enabled.group(1) for component in (
                        SERVICE, 'com.google.android.marvin.talkback/.TalkBackService'))
                    and 'touchExplorationEnabled=true' in state):
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
        # Exploration must focus this node without activating it. Capture the
        # intermediate state before dispatching a separate hardware double tap.
        explore_log = gesture_input(x, y, 'explore')
        time.sleep(0.8)
        explored = snapshot()
        result.setdefault('talkBackExplorations', []).append({
            'title': title, 'inputEvents': explore_log,
            'focusedLabels': [item.get('content-desc') or item.get('text')
                              for item in explored.iter('node')
                              if item.get('accessibility-focused') == 'true'],
            'fixtureTextUnchanged': texts(explored) == texts(tree),
        })
        focused = []
        for item in explored.iter('node'):
            if item.get('accessibility-focused') != 'true':
                continue
            if title in (item.get('text'), item.get('content-desc')):
                focused.append(item)
                continue
            # Android popup rows expose focus on the clickable row, with its
            # label on a non-actionable child. Require that exact subtree and
            # hit bounds; a focused screen/root containing the label is invalid.
            labels = [child for child in item.iter('node') if child is not item
                      and title in (child.get('text'), child.get('content-desc'))]
            bounds = list(map(int, re.findall(r'\d+', item.get('bounds', ''))))
            if (item.get('clickable') == 'true' and len(labels) == 1
                    and labels[0].get('clickable') == 'false'
                    and len(bounds) == 4
                    and bounds[0] <= int(x) < bounds[2]
                    and bounds[1] <= int(y) < bounds[3]):
                focused.append(item)
        capture(f'talkback-explored-{len(result.get("talkBackInputs", []))}')
        if not focused:
            raise AssertionError(f'Hardware exploration did not focus {title}')
        if texts(explored) != texts(tree):
            raise AssertionError(f'Exploration changed fixture content before activation: {title}')
        input_log = gesture_input(x, y, 'hold' if hold else 'activate')
        after = wait_bound()
        result.setdefault('talkBackInputs', []).append({
            'title': title, 'bounds': node.get('bounds'),
            'gesture': 'explore then double-tap-and-hold' if hold else 'explore then double-tap',
            'accessibilityBefore': before, 'accessibilityAfter': after,
            'explorationEvents': explore_log, 'inputEvents': input_log,
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
        # The first-run prompt can appear asynchronously after the service binds.
        # Observe readiness and the exact prompt together, not in a one-shot check.
        ready_since = None
        prompt_attempts = 0
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            tree = snapshot()
            permission = next((node for node in tree.iter('node')
                               if node.get('resource-id') == 'com.android.permissioncontroller:id/permission_message'
                               and 'Android Accessibility Suite' in node.get('text', '')), None)
            if permission is not None:
                ready_since = None
                deny = next((node for node in tree.iter('node')
                             if node.get('resource-id') in (
                                 'com.android.permissioncontroller:id/permission_deny_button',
                                 'com.android.permissioncontroller:id/permission_deny_and_dont_ask_again_button')), None)
                if deny is not None:
                    if prompt_attempts == 2:
                        raise AssertionError('TalkBack notification prompt did not dismiss')
                    capture(f'talkback-permission-{prompt_attempts}')
                    activate(tree, deny.get('text'))
                    prompt_attempts += 1
                    result['talkBackNotificationPromptActionAttempts'] = prompt_attempts
            elif headings[target] in texts(tree):
                if ready_since is None:
                    ready_since = time.monotonic()
                elif time.monotonic() - ready_since >= 2:
                    break
            else:
                ready_since = None
            time.sleep(0.5)
        else:
            raise AssertionError('TalkBack fixture did not become stable after service startup')
        if prompt_attempts:
            result['talkBackNotificationPromptDismissed'] = True
            capture('talkback-permission-dismissed')
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
        # The parent retains its earlier scroll offset; its introductory text
        # may be offscreen. Its exact fixture entry proves the owning page.
        tree = wait_text(entry_title)
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
