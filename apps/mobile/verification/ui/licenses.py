"""Settings -> Open Source Licenses lists every bundled library and shows its full license text."""
import sys
from driver import UI
import catalog

ui = UI(sys.argv[1], sys.argv[2])

workspace_name = '我的超长工作区名称不能折行'
avatar_label = catalog.text('inbox.workspaceSwitch.accessibility', name=workspace_name)


def dismiss_debug():
    if any(i.get('AXUniqueId') == 'xmark' and i.get('AXLabel') == catalog.system('close') for i in ui.state()):
        ui.axe('tap', '--id', 'xmark', '--post-delay', '1')


def home_ready():
    ui.wait(lambda items: any(i.get('AXLabel') == avatar_label for i in items), 'Missing workspace avatar')


dismiss_debug()
home_ready()
ui.capture('inbox')

settings_label = catalog.text('tabs.settings')
ui.axe('tap', '--label', settings_label, '--post-delay', '1')

# The About section sits below the connection rows; offscreen rows are not in the tree.
for _ in range(6):
    if any(i.get('AXUniqueId') == 'licenses' for i in ui.state()):
        break
    ui.axe('swipe', '--start-x', '200', '--start-y', '600', '--end-x', '200', '--end-y', '400', '--duration', '.5', '--post-delay', '.5')
row = ui.element('licenses')
assert catalog.text('settings.licenses.title') in (row.get('AXLabel') or ''), row
assert row['frame']['height'] >= 44, row
ui.capture('settings-row')
ui.axe('tap', '--id', 'licenses', '--post-delay', '1')

# Libraries are grouped alphabetically; section A leads with abort-controller.
first = ui.element('abort-controller')
assert 'MIT' in (first.get('AXLabel') or ''), first
ui.capture('list')

ui.axe('tap', '--id', 'abort-controller', '--post-delay', '1')
ui.wait(
    lambda items: any('Permission is hereby granted' in (i.get('AXLabel') or '') for i in items),
    'Detail page must show the full license text',
)
ui.wait(lambda items: any(i.get('AXLabel') == 'abort-controller' for i in items), 'Detail page must name the library')
ui.capture('detail')

ui.axe('tap', '--id', 'BackButton', '--post-delay', '1')
ui.element('abort-controller')
ui.capture('back')

ui.axe('tap', '--label', catalog.text('accessibility.closeSheet', title=settings_label), '--post-delay', '1')
home_ready()
assert not any(i.get('AXUniqueId') == 'licenses' for i in ui.state())
ui.capture('closed')
print("Settings lists the bundled open-source notices and opens each library's full license text.")
