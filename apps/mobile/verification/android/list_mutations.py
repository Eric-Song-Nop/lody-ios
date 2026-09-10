"""Keep a visible history row anchored while rows above it are inserted/removed."""
import re
import time


def run(shell, wait_text, tap_button, capture, texts, result, tree, appearance):
    result['appearance'] = appearance

    def bounds(node):
        return tuple(map(int, re.findall(r'\d+', node.get('bounds'))))

    def recycler(tree):
        return next(node for node in tree.iter('node') if node.get('class') == 'androidx.recyclerview.widget.RecyclerView')

    def position(tree, title):
        row = next(node for node in tree.iter('node') if node.get('content-desc') == title)
        return bounds(row)[1] - bounds(recycler(tree))[1]

    def settled(title, offset):
        deadline = time.monotonic() + 15
        while True:
            tree = wait_text(title)
            actual = position(tree, title)
            if abs(actual - offset) <= 2:
                return tree
            if time.monotonic() >= deadline:
                raise AssertionError(f'Visible row moved after snapshot: {title}: {offset} -> {actual}')
            time.sleep(0.5)

    tap_button(wait_text('LodyKit: Android'), 'Open navigation verification')
    for host in ('page', 'sheet'):
        if host == 'sheet':
            tap_button(wait_text('Offline navigation: projects'), 'Settings')
        root = 'Offline navigation: projects' if host == 'page' else 'Offline navigation: settings'
        tap_button(wait_text(root), f'Open lists {host}')
        tree = wait_text('Native grouped rows')
        left, top, right, bottom = bounds(recycler(tree))
        x = (left + right) // 2
        for _ in range(2):
            shell('input', 'swipe', str(x), str(bottom - 100), str(x), str(top + 100), '400')
        tree = wait_text('History row')
        rows = [node for node in tree.iter('node')
                if re.fullmatch(r'History row \d+', node.get('content-desc', ''))
                and bounds(node)[1] > top and bounds(node)[3] < bottom]
        if not rows:
            raise AssertionError('No fully visible history row after scrolling')
        title = rows[0].get('content-desc')
        row_id = 'row-' + title.rsplit(' ', 1)[1]
        offset = position(tree, title)
        capture(f'mutations-{host}-before')
        tap_button(tree, 'Prepend history')
        wait_text('Remove prepended rows')
        tree = settled(title, offset)
        capture(f'mutations-{host}-inserted')
        tap_button(tree, title)
        tree = wait_text(f'Last row: {row_id}')
        wait_text('Actions: 1; returns: 0; refreshes: 0')
        tap_button(tree, 'Remove prepended rows')
        wait_text('Prepend history')
        tree = settled(title, offset)
        capture(f'mutations-{host}-removed')
        tap_button(tree, title)
        tree = wait_text('Actions: 2; returns: 0; refreshes: 0')
        if f'Last row: {row_id}' not in texts(tree):
            raise AssertionError('Rebound row dispatched another identity')
        shell('input', 'keyevent', 'KEYCODE_BACK')
        tree = wait_text(root)
        if 'Prepend history' in texts(tree):
            raise AssertionError('Native list remained open after Back')
        capture(f'mutations-{host}-closed')
        result['checks'].append({
            'id': f'A-UI-01-mutations-{host}', 'status': 'pass',
            'detail': 'Prepending/removing 20 rows preserves visible anchor and current row action identity',
            'rowId': row_id, 'offsetPixels': offset,
        })
