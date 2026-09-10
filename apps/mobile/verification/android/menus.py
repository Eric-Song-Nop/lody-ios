"""Native menu actions, cancellation and owner teardown in both presentation hosts."""
import re


def run(shell, wait_text, tap_button, capture, texts, result, tree, appearance):
    tap_button(tree, 'Open navigation verification')
    for host in ('page', 'sheet'):
        if host == 'page':
            tap_button(wait_text('Offline navigation: projects'), 'Open menus page')
        else:
            tap_button(wait_text('Offline navigation: projects'), 'Settings')
            tap_button(wait_text('Offline navigation: settings'), 'Open menus sheet')
        tree = wait_text('Native Android menus')
        if f'Appearance: {appearance}' not in texts(tree):
            raise AssertionError('Menu fixture has incorrect appearance')
        tap_button(tree, 'Choose item filter')
        tree = wait_text('Recent items')
        capture(f'menus-{host}-initial')
        tap_button(tree, 'Recent items')
        tree = wait_text('Selected: recent; selections: 1')
        tap_button(tree, 'Choose item filter')
        tree = wait_text('Recent items')
        for title, expected in (('All items', 'false'), ('Recent items', 'true')):
            rows = [node for node in tree.iter('node') if node.get('resource-id', '').endswith('/content') and any(child.get('text') == title for child in node.iter('node'))]
            if len(rows) != 1 or not any(child.get('checkable') == 'true' and child.get('checked') == expected for child in rows[0].iter('node')):
                raise AssertionError(f'Incorrect selected state for {title}')
        capture(f'menus-{host}-selected')
        shell('input', 'keyevent', 'KEYCODE_BACK')
        tree = wait_text('Selected: recent; selections: 1')
        tap_button(tree, 'Change filter after delay')
        tap_button(wait_text('Selected: recent; selections: 1'), 'Choose item filter')
        wait_text('Recent items')
        tree = wait_text('Selected: all; selections: 1')
        if 'Recent items' in texts(tree):
            raise AssertionError('Menu survived replacement of its action snapshot')
        capture(f'menus-{host}-replaced')
        tap_button(tree, 'Context item')
        tree = wait_text('Action: none; actions: 0; child presses: 1')
        child = next(node for node in tree.iter('node') if node.get('text') == 'Context item' or node.get('content-desc') == 'Context item')
        x1, y1, x2, y2 = map(int, re.findall(r'\d+', child.attrib['bounds']))
        x, y = str((x1+x2)//2), str((y1+y2)//2)
        shell('input', 'touchscreen', 'swipe', x, y, x, y, '800')
        tree = wait_text('Remove item')
        capture(f'menus-{host}-context')
        tap_button(tree, 'Remove item')
        tree = wait_text('Action: remove; actions: 1; child presses: 1')
        tap_button(tree, 'Remove anchors after delay')
        tap_button(wait_text('Anchors: visible'), 'Choose item filter')
        wait_text('Recent items')
        tree = wait_text('Anchors: removed')
        if 'Recent items' in texts(tree) or 'All items' in texts(tree):
            raise AssertionError('Menu survived removal of its native anchor')
        wait_text('Selected: all; selections: 1')
        wait_text('Action: remove; actions: 1; child presses: 1')
        capture(f'menus-{host}-removed')
        tap_button(tree, 'Restore anchors')
        tree = wait_text('Anchors: visible')
        tap_button(tree, 'Remove anchors after delay')
        child = next(node for node in tree.iter('node') if node.get('text') == 'Context item' or node.get('content-desc') == 'Context item')
        x1, y1, x2, y2 = map(int, re.findall(r'\d+', child.attrib['bounds']))
        x, y = str((x1+x2)//2), str((y1+y2)//2)
        shell('input', 'touchscreen', 'swipe', x, y, x, y, '800')
        wait_text('Remove item')
        tree = wait_text('Anchors: removed')
        if 'Remove item' in texts(tree):
            raise AssertionError('Context menu survived removal of its native anchor')
        capture(f'menus-{host}-context-removed')
        tap_button(tree, 'Restore anchors')
        tree = wait_text('Anchors: visible')
        tap_button(tree, 'Choose item filter')
        tap_button(wait_text('Recent items'), 'Recent items')
        wait_text('Selected: recent; selections: 2')
        wait_text('Action: remove; actions: 1; child presses: 1')
        capture(f'menus-{host}-passed')
        shell('input', 'keyevent', 'KEYCODE_BACK')
        wait_text('Offline navigation: projects' if host == 'page' else 'Offline navigation: settings')
        result['checks'].append({'id': f'A-UI-01-menus-{host}', 'status': 'pass', 'detail': 'Selection IDs/counts, native checked state, back cancellation, child tap versus context long press, destructive action and anchor removal/recreation'})
