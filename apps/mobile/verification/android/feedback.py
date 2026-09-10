"""Real native transient surfaces in Activity and formSheet windows."""
import time


def run(shell, wait_text, tap_button, capture, texts, result, tree, appearance):
    def absent(value):
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            current = wait_text('Native Android feedback')
            if value not in texts(current):
                return current
        raise AssertionError(f'Native feedback did not expire: {value}')

    def close_notice(current, title):
        button = next(node for node in current.iter('node') if node.get('class') == 'android.widget.ImageButton' and title in node.get('content-desc', ''))
        tap_button(current, button.get('content-desc'))

    tap_button(tree, 'Open navigation verification')
    for host in ('page', 'sheet'):
        if host == 'page':
            tap_button(wait_text('Offline navigation: projects'), 'Open feedback page')
        else:
            tap_button(wait_text('Offline navigation: projects'), 'Settings')
            tap_button(wait_text('Offline navigation: settings'), 'Open feedback sheet')
        tree = wait_text('Native Android feedback')
        if f'Appearance: {appearance}; presses: 0' not in texts(tree):
            raise AssertionError('Wrong feedback fixture appearance or state')
        tap_button(tree, 'Show info toast')
        tree = wait_text('Saved locally — 本机保存 100%')
        capture(f'feedback-{host}-info')
        tree = absent('Saved locally — 本机保存 100%')
        tap_button(tree, 'Show toast burst')
        tree = wait_text('Burst four')
        visible = [node.get('text') for node in tree.iter('node') if node.get('text', '').startswith('Burst ')]
        if sorted(visible) != ['Burst four', 'Burst three', 'Burst two']:
            raise AssertionError(f'Expected bounded three notices and no duplicate: {visible}')
        capture(f'feedback-{host}-burst')
        tree = absent('Burst four')
        tap_button(tree, 'Show completed banner')
        wait_text('Offline reply completed')
        capture(f'feedback-{host}-completed')
        tree = absent('Offline reply completed')
        tap_button(tree, 'Show attention banner')
        tree = wait_text('Offline approval required')
        tap_button(tree, 'Page still interactive')
        wait_text(f'Appearance: {appearance}; presses: 1')
        time.sleep(5)
        tree = wait_text('Offline approval required')
        capture(f'feedback-{host}-sticky')
        tap_button(tree, 'Dismiss session banner')
        tree = absent('Offline approval required')
        tap_button(tree, 'Show attention banner')
        wait_text('Offline approval required')
        shell('input', 'keyevent', 'KEYCODE_HOME')
        time.sleep(1)
        shell('am', 'start', '-W', '-n', 'app.innei.lody/.MainActivity')
        tree = wait_text('Native Android feedback')
        if 'Offline approval required' in texts(tree):
            raise AssertionError('Background feedback was replayed on foreground')
        tap_button(tree, 'Show attention banner')
        wait_text('Offline approval required')
        shell('input', 'keyevent', 'KEYCODE_BACK')
        target = 'Offline navigation: projects' if host == 'page' else 'Offline navigation: settings'
        tree = wait_text(target)
        if 'Offline approval required' not in texts(tree):
            raise AssertionError('Sticky banner did not migrate to the returning window')
        capture(f'feedback-{host}-returned')
        close_notice(tree, 'Offline approval required')
        tree = wait_text(target)
        if 'Offline approval required' in texts(tree):
            raise AssertionError('Native close action did not dismiss the banner')
        result['checks'].append({'id': f'A-UI-01-feedback-{host}', 'status': 'pass', 'detail': 'Native Unicode toast, bounded/coalesced burst, native deadlines, sticky attention, explicit dismissal, touch pass-through, background cleanup and window migration'})
