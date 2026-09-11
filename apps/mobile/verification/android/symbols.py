"""Inspect the real native glyph corpus and exercise reused symbol buttons."""
import json
from pathlib import Path
import re

CORPUS = Path(__file__).resolve().parents[2] / 'src/features/debug/androidSymbols.json'


def run(shell, wait_text, tap_button, capture, texts, result, tree, appearance, host):
    names = json.loads(CORPUS.read_text())
    assert len(names) == 39 and len(set(names)) == 39, 'Update symbol fixture version and review scope when changing the corpus'
    densities = re.findall(r'density:\s*(\d+)', shell('wm', 'density'), re.I)
    if not densities:
        raise AssertionError('No device density for native symbol targets')
    density = int(densities[-1]) / 160
    result.update(host=host, appearance=appearance, symbolCorpus=names, densityScale=density)
    tap_button(tree, 'Open navigation verification')
    if host == 'sheet':
        tap_button(wait_text('Offline navigation: projects'), 'Settings')
    root = 'Offline navigation: projects' if host == 'page' else 'Offline navigation: settings'
    tap_button(wait_text(root), f'Open symbols {host}')
    for batch in range(7):
        tree = wait_text(f'Batch {batch + 1}/7 · {appearance}')
        group = names[batch * 6:(batch + 1) * 6]
        for symbol in group:
            node = next(n for n in tree.iter('node') if n.get('content-desc') == f'Activate {symbol}')
            left, top, right, bottom = map(int, re.findall(r'\d+', node.get('bounds')))
            if min(right-left, bottom-top) / density < 48:
                raise AssertionError(f'Symbol target clipped or below 48 dp: {symbol}')
        tap_button(tree, f'Activate {group[-1]}')
        tree = wait_text(f'Pressed: {group[-1]}')
        capture(f'symbols-{host}-{batch+1}')
        if batch < 6:
            tap_button(tree, 'Next symbols')
        else:
            button = next(n for n in tree.iter('node') if n.get('text') == 'Next symbols' or n.get('content-desc') == 'Next symbols')
            if button.get('enabled') != 'false':
                raise AssertionError('Final symbol batch did not disable Next')
    shell('input', 'keyevent', 'KEYCODE_BACK')
    tree = wait_text(root)
    if 'Native symbol catalog' in texts(tree):
        raise AssertionError('Symbol host remained after Back')
    result['checks'].append({'id': f'A-UI-01-symbols-{host}', 'status': 'pass',
                             'detail': '39 native glyphs captured, 48 dp targets and reused-button action identity checked; visual review required for glyph semantics'})
