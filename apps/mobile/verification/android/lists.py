"""Real native grouped rows in page/sheet hosts, without Cloud."""
import re


def run(shell, wait_text, tap_button, capture, texts, result, tree, appearance):
    result['appearance'] = appearance
    density = int(re.findall(r'density:\s*(\d+)', shell('wm', 'density'), re.IGNORECASE)[-1]) / 160
    tap_button(tree, 'Open navigation verification')
    wait_text('Offline navigation: projects')
    for host in ('page', 'sheet'):
        if host == 'sheet':
            tap_button(wait_text('Offline navigation: projects'), 'Settings')
        root = 'Offline navigation: projects' if host == 'page' else 'Offline navigation: settings'
        tap_button(wait_text(root), f'Open lists {host}')
        tree = wait_text('Native grouped rows')
        native = next(node for node in tree.iter('node') if node.get('content-desc') == 'Count action, 0')
        x1, y1, x2, y2 = map(int, re.findall(r'\d+', native.get('bounds')))
        if (y2-y1)/density < 48 or native.get('clickable') != 'true':
            raise AssertionError('Native action row lacks a 48 dp clickable target')
        capture(f'lists-{host}-initial')
        tap_button(tree, 'Count action, 0')
        tree = wait_text('Actions: 1; returns: 0; refreshes: 0')
        tap_button(tree, 'Read-only information, This row must not dispatch, Local')
        wait_text('Actions: 1; returns: 0; refreshes: 0')
        tap_button(tree, 'Update row')
        tree = wait_text('Updated action')
        tap_button(tree, 'Updated action, 1')
        tree = wait_text('Actions: 2; returns: 0; refreshes: 0')
        tap_button(tree, 'Open list detail, 原生导航行 · Native navigation')
        wait_text('Native list detail')
        shell('input', 'keyevent', 'KEYCODE_BACK')
        tree = wait_text('Actions: 2; returns: 1; refreshes: 0')
        capture(f'lists-{host}-returned')
        # A native pull gesture must invoke the controlled refresh callback once.
        node = next(node for node in tree.iter('node') if node.get('class') == 'androidx.recyclerview.widget.RecyclerView')
        left, top, right, bottom = map(int, re.findall(r'\d+', node.get('bounds')))
        x = (left+right)//2
        shell('input', 'swipe', str(x), str(top+60), str(x), str(top+500), '500')
        tree = wait_text('Actions: 2; returns: 1; refreshes: 1')
        # Exercise actual scrolling and recycling, then remove and restore the dataset.
        shell('input', 'swipe', str(x), str(bottom-100), str(x), str(top+100), '400')
        capture(f'lists-{host}-scrolled')
        tree = wait_text('Actions: 2; returns: 1; refreshes: 1')
        if 'History row' not in texts(tree):
            raise AssertionError('Native list did not scroll into history rows')
        tap_button(tree, 'Empty list')
        tree = wait_text('No local rows')
        if 'History row' in texts(tree):
            raise AssertionError('Deleted native rows survived the empty snapshot')
        capture(f'lists-{host}-empty')
        tap_button(tree, 'Restore list')
        tree = wait_text('Updated action')
        tap_button(tree, 'Updated action, 2')
        wait_text('Actions: 3; returns: 1; refreshes: 1')
        capture(f'lists-{host}-passed')
        shell('input', 'keyevent', 'KEYCODE_BACK')
        wait_text(root)
        result['checks'].append({'id': f'A-UI-01-lists-{host}', 'status': 'pass', 'detail': 'Native action/static rows, ID-preserving update, navigation return, refresh, scrolling and empty/restore snapshots'})
