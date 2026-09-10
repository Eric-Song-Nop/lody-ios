"""Real Android application locale changes without resetting the active route."""
import re
import time

PACKAGE = 'app.innei.lody'


def run(shell, wait_text, tap_button, capture, texts, result, tree, appearance, host):
    result.update(appearance=appearance, host=host)

    def get_locales():
        raw = shell('cmd', 'locale', 'get-app-locales', PACKAGE, '--user', '0')
        match = re.search(r'\[([^\]]*)\]', raw)
        if not match:
            raise AssertionError(f'Cannot read real app locales: {raw}')
        return match.group(1)

    def set_locales(value):
        # Omitting --locales clears the override; adb shell drops empty argv.
        arguments = ['cmd', 'locale', 'set-app-locales', PACKAGE, '--user', '0']
        if value:
            arguments.extend(['--locales', value])
        shell(*arguments)
        actual = get_locales()
        if actual != value:
            raise AssertionError(f'App locales did not change: {actual!r} != {value!r}')

    original = get_locales()
    result['originalAppLocales'] = original
    try:
        set_locales('en-US')
        tap_button(wait_text('LodyKit: Android'), 'Open navigation verification')
        tree = wait_text('Offline navigation: projects')
        if host == 'sheet':
            tap_button(tree, 'Settings')
            tree = wait_text('Offline navigation: settings')
        tap_button(tree, f'Open language switching {host}')
        tree = wait_text('Language snapshot: en')
        tap_button(tree, 'Language draft')
        shell('input', 'text', 'Retained-draft-42')
        shell('input', 'keyevent', 'KEYCODE_BACK')
        tree = wait_text('Retained-draft-42')
        native_close = next(node for node in tree.iter('node') if node.get('content-desc') == 'Close' and node.get('clickable') == 'true')
        tap_button(native_close, 'Close')
        tree = wait_text('Native presses: 1')
        process = shell('pidof', PACKAGE)
        if not process:
            raise AssertionError('Missing running app process')
        result['initialProcess'] = process

        def check(language, close, one, many, name):
            tree = wait_text(f'Language snapshot: {language}')
            text = texts(tree)
            for expected in [one, many, 'Native presses: 1']:
                if expected not in text:
                    raise AssertionError(f'Missing localized or retained state: {expected}')
            if not any(node.get('class') == 'android.widget.EditText' and node.get('text') == 'Retained-draft-42' for node in tree.iter('node')):
                raise AssertionError('Editable draft was lost during locale change')
            if not any(node.get('content-desc') == close and node.get('clickable') == 'true' for node in tree.iter('node')):
                raise AssertionError(f'Native default accessibility label did not update: {close}')
            if host == 'sheet':
                prefix = '关闭' if language == 'zh-Hans' else 'Close '
                expected_header = prefix + 'Language switching'
                if not any(node.get('content-desc') == expected_header for node in tree.iter('node')):
                    raise AssertionError(f'Sheet close label did not update: {expected_header}')
            if shell('pidof', PACKAGE) != process:
                raise AssertionError('App process restarted during language switch')
            capture(name)
            window_dump = shell('dumpsys', 'window', 'displays')
            match = re.search(r'mLastStatusBarAppearanceRegions=\n((?:[ \t]+AppearanceRegion\{[^\n]*\}\n)+)', window_dump)
            if not match:
                raise AssertionError('Missing system status bar appearance regions')
            regions = match.group(1).strip().splitlines()
            result.setdefault('statusBarChecks', []).append({
                'state': name, 'regions': regions, 'windowDisplayDump': window_dump,
            })
            wants_dark_icons = appearance == 'light'
            if any(('LIGHT_STATUS_BARS' in region) != wants_dark_icons for region in regions):
                raise AssertionError(f'Status bar icon contrast changed in {name}: {regions}')

        check('en', 'Close', '1 computer', '2 computers', 'language-en')
        set_locales('zh-Hans-CN')
        check('zh-Hans', '关闭', '1 台电脑', '2 台电脑', 'language-zh')
        shell('input', 'keyevent', 'KEYCODE_HOME')
        set_locales('es-ES')
        shell('am', 'start', '-W', '-n', f'{PACKAGE}/.MainActivity')
        check('en', 'Close', '1 computer', '2 computers', 'language-fallback-return')
        set_locales('en-US')
        check('en', 'Close', '1 computer', '2 computers', 'language-en-return')
        ime_shown = 'mInputShown=true' in shell('dumpsys', 'input_method')
        result['imeShownBeforeReturn'] = ime_shown
        if ime_shown:
            shell('input', 'keyevent', 'KEYCODE_BACK')
            wait_text('Runtime language verification')
            if 'mInputShown=true' in shell('dumpsys', 'input_method'):
                raise AssertionError('First back did not dismiss the keyboard')
        shell('input', 'keyevent', 'KEYCODE_BACK')
        destination = f'Offline navigation: {"settings" if host == "sheet" else "projects"}'
        deadline = time.monotonic() + 30
        while True:
            returned = wait_text(destination)
            if 'Runtime language verification' not in texts(returned):
                break
            if time.monotonic() >= deadline:
                raise AssertionError('Destination is behind an undismissed language page')
            time.sleep(0.5)
        capture('language-dismissed')
        result['checks'].append({'id': f'A-UI-01-language-switch-{host}', 'status': 'pass', 'detail': 'Real app locale en→zh→es fallback→en; independently subscribed memoized text and native close label update; draft, counter, process and return destination retained, including background/foreground; translated sheet close label and active route removal after IME-aware back'})
    finally:
        set_locales(original)
        result['appLocalesRestored'] = original
