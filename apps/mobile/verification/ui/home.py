"""Home uses navigation search and the trailing tab opens creation without changing tabs."""
import sys
from driver import UI
import catalog

ui = UI(sys.argv[1], sys.argv[2])


def commit(text):
    ui.axe('type', text)
    # A Chinese App Language brings up the pinyin IME, which holds Latin letters as
    # composition until Return commits them verbatim.
    if catalog.LANGUAGE != 'en':
        ui.axe('key', '40')

ui.element('new-session-tab')
if any(i.get('AXUniqueId') == 'xmark' and i.get('AXLabel') == catalog.system('close') for i in ui.state()):
    ui.axe('tap', '--id', 'xmark', '--post-delay', '1')
ui.capture('home')
ui.axe('tap', '--id', 'new-session-tab', '--post-delay', '1')
ui.element('create-session-input')
ui.capture('create')
# Expand from the sheet's header, leaving the production form untouched.
label = catalog.text('accessibility.closeSheet', title=catalog.text('create.title'))
header = next(item['frame'] for item in ui.state() if item.get('AXLabel') == label)
ui.axe('swipe', '--start-x', '200', '--start-y', str(header['y'] + 10),
       '--end-x', '200', '--end-y', '100', '--duration', '.6', '--post-delay', '.8')
expanded_header = next(item['frame'] for item in ui.state() if item.get('AXLabel') == label)
assert expanded_header['y'] < header['y'] - 100, 'Creation sheet did not expand to the full detent'
ui.capture('create-full')

ui.axe('tap', '--label', catalog.text('accessibility.closeSheet', title=catalog.text('create.title')), '--post-delay', '1')
ui.element('new-session-tab')
assert any(i.get('AXLabel') == catalog.text('tabs.sessions') and str(i.get('AXValue')) == '1' for i in ui.state())
ui.axe('tap', '--id', 'new-session-tab', '--post-delay', '1')
ui.element('create-session-input')
ui.axe('tap', '--label', catalog.text('accessibility.closeSheet', title=catalog.text('create.title')), '--post-delay', '1')
ui.capture('returned')
ui.axe('tap', '--value', catalog.text('search.field.placeholder'), '--post-delay', '.5')
commit('Search')
ui.element('ui-search')
assert not any(i.get('AXUniqueId') == 'ui-design' for i in ui.state())
ui.capture('search')
ui.axe('tap', '--label', catalog.system('clear'))
commit('Lody')
ui.element('project:ui:unassigned')
ui.capture('project-search')
ui.axe('tap', '--label', catalog.system('clear'))
commit('NoSuchSession')
ui.wait(lambda items: any(i.get('AXLabel') == catalog.text('search.placeholder.noMatch') for i in items), 'Missing empty search state')
ui.capture('empty-search')
ui.axe('tap', '--label', catalog.system('close'), '--post-delay', '1')
ui.element('ui-design')
assert not any(i.get('AXUniqueId') == 'ui-search' for i in ui.state())
ui.capture('cancelled')
ui.axe('tap', '--label', catalog.text('tabs.settings'), '--post-delay', '1')
ui.axe('tap', '--id', 'new-session-tab', '--post-delay', '1')
ui.element('create-session-input')
ui.axe('tap', '--label', catalog.text('accessibility.closeSheet', title=catalog.text('create.title')), '--post-delay', '1')
assert any(i.get('AXLabel') == catalog.text('tabs.settings') and str(i.get('AXValue')) == '1' for i in ui.state())
ui.capture('settings-returned')
for kind in ('machine', 'agent', 'mcp'):
    row = ui.element(f'remote-{kind}')
    assert catalog.text(f'settings.remote.{kind}') in (row.get('AXLabel') or '')
    assert row['frame']['height'] >= 44
    ui.axe('tap', '--id', f'remote-{kind}', '--post-delay', '.5')
    ui.element('retry')
    ui.wait(lambda items: any(catalog.text('settings.remote.loadFailed') in (item.get('AXLabel') or '') for item in items), 'Remote settings must show a recoverable offline error')
    ui.capture(f'remote-{kind}')
    ui.axe('tap', '--label', catalog.text('tabs.settings'), '--element-type', 'Button', '--post-delay', '.5')
    ui.element(f'remote-{kind}')
row = ui.element('archived')
assert catalog.text('settings.archived.title') in (row.get('AXLabel') or '')
ui.axe('tap', '--id', 'archived', '--post-delay', '.8')
archived = ui.element('ui-search')
spoken = ' '.join((i.get('AXLabel') or '') for i in [archived, *(archived.get('children') or [])])
assert '搜索历史会话 Search' in spoken and catalog.text('inbox.badge.archived') in spoken, spoken
assert archived['frame']['height'] >= 44
assert not any(i.get('AXUniqueId') == 'ui-design' for i in ui.state())
ui.capture('archived-sessions')
ui.axe('tap', '--label', catalog.text('tabs.settings'), '--element-type', 'Button', '--post-delay', '.5')
ui.element('archived')
print('Trailing create opens repeatedly without changing tabs; navigation search finds archived sessions and cancels back to the inbox.')
