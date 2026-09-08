import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { openTestSession } from '../helpers.mjs';
import { firstPermissionTarget } from '../../src/features/sessions/permissionTarget.ts';

// Synthetic snapshot authored by OSS 896fd1e sessionDocSchema + Mirror 2.3.1,
// Loro 1.15.1. No account data. Unlike plain-object fixtures, nested strings
// and permission options use Mirror's actual inferred CRDT containers.
test('OSS permission snapshot carries actions through projection and writes an answer back', async (t) => {
  const { runtime, server, pushUpdate, close } = await openTestSession();
  t.after(close);
  server.import(
    await readFile(new URL('../fixtures/oss-permission.bin', import.meta.url)),
  );
  const snapshot = await pushUpdate();
  const target = firstPermissionTarget(snapshot.entries);
  assert.deepEqual(
    target.options.map((o) => o.optionId),
    ['yes', 'no'],
  );
  const detail = await runtime.itemDetail({ sessionId: 's1', ...target });
  assert.deepEqual(detail.options, target.options);
  const before = snapshot.entries[0].items[0].rev;
  const request = server
    .getList('history')
    .get(0)
    .get('items')
    .get(0)
    .get('permissionRequest');
  request.get('options').push({ optionId: 'custom', name: 'Custom choice' });
  server.commit();
  const updated = await pushUpdate();
  assert.ok(updated.entries[0].items[0].rev > before);
  assert.equal(
    firstPermissionTarget(updated.entries).options.at(-1).name,
    'Custom choice',
  );
  assert.equal(
    (
      await runtime.respondPermission({
        sessionId: 's1',
        ...target,
        optionId: 'custom',
      })
    ).state,
    'accepted',
  );
  assert.deepEqual(
    server.toJSON().history[0].items[0].permissionRequest.outcome,
    { outcome: 'selected', optionId: 'custom' },
  );
  assert.equal(
    firstPermissionTarget(runtime.projectSession(server, 'live').entries),
    undefined,
  );
});
