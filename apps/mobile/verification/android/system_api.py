"""Persist real native preferences across process death, and paste system clipboard."""


def run(shell, wait_text, tap_button, capture, texts, result, tree, appearance):
    result['appearance'] = appearance
    def open_scene(tree):
        tap_button(tree, 'Open navigation verification')
        tap_button(wait_text('Offline navigation: projects'), 'Open system APIs')
        return wait_text('Native system APIs')
    tree = open_scene(tree)
    wait_text('Initial inbox view: 0')
    wait_text('Alpha: unset; Beta: unset')
    tap_button(tree, 'Save inbox preferences')
    tree = wait_text('Alpha: true; Beta: false')
    wait_text('Preferences written: true')
    capture('system-preferences-written')
    # Process death does not clear app data; constants and SharedPreferences must reload.
    shell('am', 'force-stop', 'app.innei.lody')
    shell('am', 'start', '-W', '-n', 'app.innei.lody/.MainActivity')
    tree = open_scene(wait_text('Lody Android verification'))
    wait_text('Initial inbox view: 1')
    wait_text('Alpha: true; Beta: false')
    tap_button(tree, 'Update alpha preference')
    tree = wait_text('Alpha: false; Beta: false')
    capture('system-preferences-restored')
    tap_button(tree, 'Copy fixture text')
    tree = wait_text('Native system APIs')
    tap_button(tree, 'Paste fixture here')
    shell('input', 'keyevent', 'KEYCODE_PASTE')
    shell('input', 'keyevent', 'KEYCODE_BACK')
    wait_text('Clipboard paste matches: true')
    capture('system-clipboard-pasted')
    tree = wait_text('Clipboard paste matches: true')
    tap_button(tree, 'Request selection feedback')
    wait_text('Feedback request: resolved')
    capture('system-passed')
    result['checks'].append({'id': 'A-UI-01-system-preferences-clipboard', 'status': 'pass', 'detail': 'Native display preferences survive force-stop, isolated project updates, exact Unicode/literal clipboard paste; haptic API resolves without proving physical feedback'})
