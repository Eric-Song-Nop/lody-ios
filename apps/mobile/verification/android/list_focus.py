"""Keyboard activation and focus continuity through native row updates/return."""


def run(shell, wait_text, tap_button, capture, texts, result, tree, appearance, list_return='present'):
    result['appearance'] = appearance
    result['listSourceRow'] = list_return

    def focused(tree, prefix):
        return any(node.get('content-desc', '').startswith(prefix)
                   and node.get('focused') == 'true' for node in tree.iter('node'))

    def focus(prefix):
        tree = wait_text('Native grouped rows')
        for _ in range(16):
            if focused(tree, prefix):
                return tree
            shell('input', 'keyevent', 'KEYCODE_TAB')
            tree = wait_text('Native grouped rows')
        raise AssertionError(f'Keyboard cannot reach native row: {prefix}')

    tap_button(wait_text('LodyKit: Android'), 'Open navigation verification')
    for host in ('page', 'sheet'):
        if host == 'sheet':
            tap_button(wait_text('Offline navigation: projects'), 'Settings')
        root = 'Offline navigation: projects' if host == 'page' else 'Offline navigation: settings'
        tap_button(wait_text(root), f'Open lists {host}')
        focus('Count action, 0')
        capture(f'focus-{host}-action')
        for count in (1, 2):
            shell('input', 'keyevent', 'KEYCODE_ENTER')
            tree = wait_text(f'Actions: {count}; returns: 0; refreshes: 0')
            if not focused(tree, f'Count action, {count}'):
                raise AssertionError('Native row lost keyboard focus when its value changed')
        capture(f'focus-{host}-updated')
        # The immediately preceding actionable row is the navigation row.
        shell('input', 'keyevent', 'KEYCODE_DPAD_UP')
        tree = wait_text('Native grouped rows')
        if not focused(tree, 'Open list detail,'):
            raise AssertionError('Directional navigation did not reach the preceding native row')
        shell('input', 'keyevent', 'KEYCODE_ENTER')
        wait_text('Native list detail')
        capture(f'focus-{host}-detail')
        if list_return != 'present':
            label = {'removed': 'Remove source row', 'disabled': 'Disable source navigation'}[list_return]
            # Stay in keyboard mode while mutating the covered list's data.
            observations = []
            result.setdefault('detailKeyboardFocus', {})[host] = observations
            for step in range(12):
                tree = wait_text('Native list detail')
                observations.append({'step': step, 'focused': [dict(node.attrib) for node in tree.iter('node') if node.get('focused') == 'true']})
                if any(node.get('focused') == 'true' and label in (node.get('content-desc'), node.get('text')) for node in tree.iter('node')):
                    break
                shell('input', 'keyevent', 'KEYCODE_TAB')
            else:
                capture(f'focus-{host}-mutation-unreachable')
                raise AssertionError(f'Cannot reach detail mutation button: {label}')
            shell('input', 'keyevent', 'KEYCODE_ENTER')
            wait_text(f'Source row: {list_return}')
            capture(f'focus-{host}-source-changed')
        shell('input', 'keyevent', 'KEYCODE_BACK')
        tree = wait_text('Actions: 2; returns: 1; refreshes: 0')
        if list_return == 'present' and not focused(tree, 'Open list detail,'):
            raise AssertionError('Returning from detail lost the native navigation row focus')
        if list_return != 'present' and focused(tree, 'Open list detail,'):
            raise AssertionError('Returning from detail focused a removed or non-navigating source row')
        if list_return == 'removed' and 'Open list detail' in texts(tree):
            raise AssertionError('Removed source row still exists')
        if list_return == 'disabled' and 'Navigation unavailable' not in texts(tree):
            raise AssertionError('Source row was not changed to non-navigating content')
        capture(f'focus-{host}-returned')
        shell('input', 'keyevent', 'KEYCODE_BACK')
        tree = wait_text(root)
        if 'Native grouped rows' in texts(tree):
            raise AssertionError('Native list host remained after Back')
        result['checks'].append({
            'id': f'A-UI-01-focus-{list_return}-{host}', 'status': 'pass',
            'detail': f'Keyboard reaches native rows and preserves focus after updates; detail Back checks source row state {list_return}',
        })
