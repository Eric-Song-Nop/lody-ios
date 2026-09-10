"""Native notice placement and real input focus while the system IME is visible."""
import re
import time


def bounds(node):
    return list(map(int, re.findall(r'\d+', node.get('bounds'))))


def run(shell, wait_text, tap_button, capture, texts, result, tree, appearance, host):
    preference = 'accessibility_interactive_ui_timeout_ms'
    original = shell('settings', 'get', 'secure', preference)
    result.update(feedbackHost=host, appearance=appearance, interactiveTimeoutMs=10000)
    try:
        shell('settings', 'put', 'secure', preference, '10000')
        tap_button(tree, 'Open navigation verification')
        tree = wait_text('Offline navigation: projects')
        if host == 'sheet':
            tap_button(tree, 'Settings')
            tree = wait_text('Offline navigation: settings')
        tap_button(tree, f'Open keyboard feedback {host}')
        tree = wait_text('Feedback with keyboard')
        tap_button(tree, 'Feedback draft')
        time.sleep(1)
        tree = wait_text('Feedback with keyboard')
        input_method = shell('dumpsys', 'input_method')
        if 'mInputShown=true' not in input_method:
            raise AssertionError('System keyboard did not open')
        draft = next(n for n in tree.iter('node') if n.get('class') == 'android.widget.EditText')
        if draft.get('focused') != 'true':
            raise AssertionError('Draft did not acquire native focus')
        capture(f'feedback-keyboard-{host}-ready')
        tree = wait_text('Feedback with keyboard')
        tap_button(tree, 'Show keyboard toast')
        capture(f'feedback-keyboard-{host}-requested')
        tree = wait_text('Feedback requests: 1')
        tree = wait_text('Your draft remains available')
        keyboard_nodes = [n for n in tree.iter('node') if 'inputmethod' in n.get('package', '') and bounds(n)[3] > bounds(n)[1]]
        if not keyboard_nodes:
            raise AssertionError('No visible system keyboard hierarchy')
        keyboard_top = min(bounds(n)[1] for n in keyboard_nodes)
        close = next(n for n in tree.iter('node') if n.get('class') == 'android.widget.ImageButton' and 'Your draft remains available' in n.get('content-desc', ''))
        parents = {child: parent for parent in tree.iter('node') for child in parent}
        card = parents[close]
        card_bounds = bounds(card)
        if card_bounds[3] > keyboard_top:
            raise AssertionError(f'Notice overlaps keyboard: {card_bounds[3]} > {keyboard_top}')
        draft = next(n for n in tree.iter('node') if n.get('class') == 'android.widget.EditText')
        if draft.get('focused') != 'true' or draft.get('text') != 'Draft survives feedback':
            raise AssertionError('Feedback changed input focus or draft text')
        result['geometry'] = {'cardBounds': card_bounds, 'keyboardTop': keyboard_top}
        capture(f'feedback-keyboard-{host}-visible')
        tap_button(tree, close.get('content-desc'))
        tree = wait_text('Feedback with keyboard')
        if 'Your draft remains available' in texts(tree):
            raise AssertionError('Native close failed while keyboard was visible')
        if 'mInputShown=true' not in shell('dumpsys', 'input_method'):
            raise AssertionError('Closing feedback dismissed the keyboard')
        capture(f'feedback-keyboard-{host}-dismissed')
        shell('input', 'keyevent', 'KEYCODE_BACK')
        tree = wait_text('Feedback with keyboard')
        if 'mInputShown=true' in shell('dumpsys', 'input_method'):
            raise AssertionError('System back did not dismiss keyboard first')
        shell('input', 'keyevent', 'KEYCODE_BACK')
        wait_text(f'Offline navigation: {"projects" if host == "page" else "settings"}')
        result['checks'].append({'id': f'A-UI-01-feedback-keyboard-{host}', 'status': 'pass', 'detail': 'Native toast clears real IME; input focus and draft preserved; native close retains keyboard; system back dismisses IME before host.'})
    finally:
        if original == 'null':
            shell('settings', 'delete', 'secure', preference)
        else:
            shell('settings', 'put', 'secure', preference, original)
        if shell('settings', 'get', 'secure', preference) != original:
            raise AssertionError('Accessibility timeout preference was not restored')
        result['interactiveTimeoutRestored'] = True
