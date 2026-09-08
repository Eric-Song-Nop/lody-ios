"""Immediate offline user/timer rows, exact failed draft restore, receipt reconciliation."""
import sys
from driver import UI
import catalog
from send_motion import ThrowTrace
ui = UI(*sys.argv[1:])
throw_trace = ThrowTrace(ui)
ui.axe('tap', '--id', 'session-input')
ui.axe('type', 'Offline send\nKeep my attachment')
draft = ui.element('session-input')['AXValue']
PREVIEW = catalog.text('native.chat.attachment.preview', name='')
attachments = [i['AXLabel'] for i in ui.state() if (i.get('AXLabel') or '').startswith(PREVIEW)]
assert attachments
ui.capture('draft')
ui.axe('tap', '--id', 'session-send')
working = catalog.text('native.chat.transcript.status.workingFor', duration='')
timer = ui.wait(
    lambda items: next(
        (
            i for i in items
            if (i.get('AXUniqueId') or '').endswith(':duration')
            and (i.get('AXLabel') or '').startswith(working)
        ),
        None,
    ),
    'Offline timer row missing',
)
turn = timer['AXUniqueId'].removesuffix(':duration')
assert ui.element('send-status')['AXLabel'] == 'Calls: 0 · waiting', 'Network ran before connection'
assert draft in ui.element(turn + ':user')['AXLabel']
assert not ui.element('session-input').get('AXValue')
ui.capture('offline')
ui.axe('tap', '--id', turn + ':duration')
ui.wait(lambda items: any(i.get('AXLabel') == 'Calls: 1 · sending' for i in items), 'Connected send did not start')
ui.axe('tap', '--id', 'send-fail')
ui.wait(lambda items: any(i.get('AXLabel') == catalog.text('send.alert.title') for i in items), 'Definite failure not surfaced')
ui.capture('failure-alert')
ui.axe('tap', '--label', catalog.system('ok'))
ui.wait(lambda items: any(i.get('AXUniqueId') == 'session-input' and i.get('AXValue') == draft for i in items), 'Text was not restored')
assert [i['AXLabel'] for i in ui.state() if (i.get('AXLabel') or '').startswith(PREVIEW)] == attachments
assert not any(i.get('AXUniqueId') in [turn + ':user', turn + ':duration'] for i in ui.state()), 'Failed rows remain'
ui.capture('restored')
ui.axe('tap', '--id', 'session-send')
ui.wait(lambda items: any(i.get('AXLabel') == 'Calls: 2 · sending' for i in items), 'Explicit retry did not start')
retry_timer = ui.wait(
    lambda items: next(
        (i for i in items if (i.get('AXUniqueId') or '').endswith(':duration')),
        None,
    ),
    'Retry timer row missing',
)
turn = retry_timer['AXUniqueId'].removesuffix(':duration')
ui.axe('tap', '--id', 'send-complete')
ui.wait(lambda items: any(i.get('AXLabel') == 'Calls: 2 · accepted' for i in items), 'Receipt missing')
ui.capture('waiting-reply')
ui.axe('tap', '--id', 'send-reply')
ui.wait(lambda items: any(i.get('AXLabel') == 'Calls: 2 · idle' for i in items), 'Reply did not reconcile local pending')
handoff_timer = ui.element(turn + ':duration')
assert handoff_timer['AXLabel'].startswith(working), 'Server takeover interrupted the first timer row'
assert not any((i.get('AXUniqueId') or '').endswith(':pending') for i in ui.state())
ui.axe('tap', '--id', 'session-input')
# A digit prefix avoids keyboard Shift/autocapitalization changing AXe input.
ui.type_into('session-input', '2 next draft')
assert ui.element('session-input')['AXValue'] == '2 next draft', 'Acknowledged draft re-locked input'
ui.capture('reconciled')
ui.axe('tap', '--id', 'session-send')
ui.wait(lambda items: any(i.get('AXLabel') == 'Calls: 3 · sending' for i in items), 'Third send missing')
ui.type_into('session-input', '3 followup')
assert ui.element('session-input')['AXValue'] == '3 followup', 'Pending send dismissed or locked input'
ui.axe('tap', '--id', 'send-fail')
ui.wait(lambda items: any(i.get('AXLabel') == catalog.text('send.alert.title') for i in items), 'Failure alert missing')
ui.axe('tap', '--label', catalog.system('ok'))
assert ui.element('session-input')['AXValue'] == '3 followup', 'Failure overwrote the new draft'
assert not ui.element('session-send')['enabled'], 'Unmerged failed draft must be retained'
ui.axe('tap', '--label', catalog.text('native.chat.composer.failedDraft'))
assert ui.element('session-input')['AXValue'] == '3 followup\n\n2 next draft'
assert ui.element('session-send')['enabled']
ui.capture('merged-drafts')
print('PASS: offline immediate message/timer, explicit rejection restore with attachment, retry and uninterrupted server takeover')

throw_trace.verify(3)
