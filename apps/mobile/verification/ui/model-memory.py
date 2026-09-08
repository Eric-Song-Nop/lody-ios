"""Exercise model memory through the production creation sheet and model page."""
import sys
from driver import UI
import catalog

ui = UI(sys.argv[1], sys.argv[2])

def tap_id(value):
    ui.element(value)
    ui.axe('tap', '--id', value, '--post-delay', '.5')

def tab(key):
    ui.axe('tap', '--label', catalog.text('model.tab.' + key), '--post-delay', '.5')

def back():
    item = ui.wait(lambda items: next((i for i in items if i.get('type') == 'Button' and i.get('AXLabel') in ['Back', catalog.text('create.title')]), None), 'Back button missing')
    f = item['frame']
    ui.axe('tap', '-x', str(f['x'] + f['width']/2), '-y', str(f['y'] + f['height']/2), '--post-delay', '.5')

def summary(value):
    ui.wait(lambda items: any(value in (i.get('AXLabel') or '') for i in items), 'Missing remembered summary: ' + value)

tap_id('model')
tap_id('a')
tab('effort')
tap_id('high')
tab('mode')
tap_id('read-only')
tab('model')
tap_id('b')
back()
summary('Model B · Full Access')
ui.capture('new-model-full-access')
tap_id('model')
tap_id('b')
tab('effort')
tap_id('low')
back()
summary('Model B · low · Full Access')
# The native composer must restore A's settings, not echo its temporary empty effort.
tap_id('create-session-input')
tap_id('session-model')
tap_id('composer-model-menu')
ui.axe('tap', '--label', 'Model A', '--element-type', 'Button', '--post-delay', '.8')
summary('High')
ui.capture('native-restored-a')
ui.axe('tap', '-x', '20', '-y', '160', '--post-delay', '.5')
summary('Model A · high · Read Only')
tap_id('model')
tap_id('b')
back()
summary('Model B · low · Full Access')
ui.capture('restored-b')
print('PASS: per-model effort and permission, full-access default, both selection hosts')
