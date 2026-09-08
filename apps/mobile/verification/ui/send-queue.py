"""Accept two more messages while a reply runs, then consume them in order."""
import sys
from driver import UI
import catalog
from send_motion import ThrowTrace

ui = UI(*sys.argv[1:])
trace = ThrowTrace(ui)
ui.axe('tap', '--id', 'send-connect')
turns = []
for index in [1, 2]:
    message = f'{index} queued message'
    ui.axe('tap', '--id', 'session-input')
    ui.type_into('session-input', message)
    ui.axe('tap', '--id', 'session-send')
    ui.wait(lambda items: any(i.get('AXLabel') == f'Calls: {index} · sending' for i in items), 'Queue write did not start')
    pending = ui.wait(lambda items: next((i for i in items if (i.get('AXUniqueId') or '').endswith(':pending')), None), 'Pending row missing')
    turn = pending['AXUniqueId'].removesuffix(':pending')
    turns.append(turn)
    ui.axe('tap', '--id', 'send-complete')
    ui.wait(lambda items: any(i.get('AXLabel') == f'Calls: {index} · queued' for i in items), 'Queue receipt missing')
    assert ui.element(turn + ':queued')['AXLabel'] == catalog.text('native.chat.row.queued')
    assert ui.element('queue-count')['AXLabel'] == f'Queue: {index}'
    assert not ui.element('session-input').get('AXValue'), 'Queued draft reappeared'
    ui.capture(f'queued-{index}')
assert turns[0] != turns[1]
ui.axe('tap', '--id', 'send-reply')
ui.wait(lambda items: any(i.get('AXUniqueId') == 'queue-count' and i.get('AXLabel') == 'Queue: 1' for i in items), 'First queue item was not consumed')
ui.element(turns[1] + ':queued')
ui.capture('first-consumed-second-waiting')
ui.axe('tap', '--id', 'send-reply')
ui.wait(lambda items: any(i.get('AXLabel') == 'Calls: 2 · idle' for i in items), 'Queue did not drain')
assert ui.element('queue-count')['AXLabel'] == 'Queue: 0'
assert not any((i.get('AXUniqueId') or '').endswith(':queued') for i in ui.state())
ui.capture('queue-drained')
trace.verify(2)
print('PASS: two distinct queued messages, composer unlocked, FIFO consumption and no duplicate draft')
