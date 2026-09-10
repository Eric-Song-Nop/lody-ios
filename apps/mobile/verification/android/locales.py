"""Compare compiled Android resources to shared catalogs on the device."""
import re


def run(shell, wait_text, tap_button, capture, texts, result, tree, appearance):
    result['appearance'] = appearance
    tap_button(tree, 'Open navigation verification')
    tap_button(wait_text('Offline navigation: projects'), 'Open native languages')
    tree = wait_text('Native locales passed:')
    text = texts(tree)
    match = re.search(r'Native locales passed: (\d+) resources; 4 rejected inputs', text)
    if not match or int(match[1]) <= 0:
        raise AssertionError('Missing native compiled-resource report')
    for expected in ['en: Close', 'zh-Hans: 关闭', 'en: 0 files', 'en: 1 file', 'en: 2 files', 'es: Close']:
        if expected not in text:
            raise AssertionError(f'Missing rendered native text: {expected}')
    capture('locales-passed')
    result['resourceComparisons'] = int(match[1])
    result['checks'].append({'id': 'A-UI-01-native-locales', 'status': 'pass', 'detail': 'Every compiled native resource matches source catalogs across en/zh-Hans/es fallback, plural 0/1/2, literal parameter interpolation and four rejected invalid inputs'})
    shell('input', 'keyevent', 'KEYCODE_BACK')
    wait_text('Offline navigation: projects')
