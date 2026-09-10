import assert from 'node:assert/strict';
import test from 'node:test';
import vm from 'node:vm';
import { build } from 'esbuild';

const { outputFiles } = await build({
  entryPoints: ['apps/mobile/modules/lody-kit/data-runtime/host.ts'],
  bundle: true,
  format: 'iife',
  globalName: 'host',
  write: false,
});
const load = (globals) => {
  const context = vm.createContext(globals);
  vm.runInContext(outputFiles[0].text, context);
  return context;
};

test('Android bridge reassembles large Unicode events without changing their JSON', () => {
  const chunks = [];
  const context = load({
    lodyDataHost: {
      postChunk: (...chunk) => {
        chunks.push(chunk);
        return true;
      },
    },
  });
  const event = { type: 'catalog', catalog: '中文👩🏽‍💻'.repeat(12000) };
  context.host.sendToHost(event);
  assert.ok(chunks.length > 1);
  assert.ok(
    chunks.every(
      ([id, index, total, value], position) =>
        id === 1 &&
        index === position &&
        total === chunks.length &&
        value.length <= 32768,
    ),
  );
  assert.deepEqual(JSON.parse(chunks.map((chunk) => chunk[3]).join('')), event);
});

test('Android stops on rejected admission and explicitly reports oversized output', () => {
  let calls = 0;
  const rejected = load({
    lodyDataHost: {
      postChunk: () => {
        calls++;
        return false;
      },
    },
  });
  assert.throws(
    () => rejected.host.sendToHost({ text: 'x'.repeat(70000) }),
    /bridge_rejected/,
  );
  assert.equal(calls, 1);
  const messages = [];
  const limited = load({
    lodyDataHost: {
      postChunk: (_id, _index, _total, value) => {
        messages.push(JSON.parse(value));
        return true;
      },
    },
  });
  assert.throws(
    () => limited.host.sendToHost({ text: 'x'.repeat(4 * 1024 * 1024) }),
    /bridge_limit/,
  );
  assert.deepEqual(messages, [{ type: 'bridgeError', reason: 'bridge_limit' }]);
});

test('iOS keeps its existing object-message contract', () => {
  let received;
  const context = load({
    webkit: {
      messageHandlers: {
        dataRuntime: {
          postMessage: (value) => {
            received = value;
          },
        },
      },
    },
  });
  const event = { type: 'grant' };
  context.host.sendToHost(event);
  assert.equal(received, event);
});

test('Android command responses retain request IDs and suppress sensitive exceptions', async () => {
  const messages = [];
  const context = load({
    lodyDataHost: {
      postChunk: (_id, _index, _total, value) => {
        messages.push(JSON.parse(value));
        return true;
      },
    },
    dataRuntime: {
      ping: () => true,
      broken: () => {
        throw new Error('secret-token');
      },
    },
  });
  await context.lodyRuntimeInvoke(7, 'ping', []);
  await context.lodyRuntimeInvoke(8, 'broken', []);
  await context.lodyRuntimeInvoke(9, 'constructor', []);
  assert.deepEqual(messages, [
    { type: 'rpc', id: 7, result: true },
    { type: 'rpc', id: 8, error: 'runtime_command_failed' },
    { type: 'rpc', id: 9, error: 'runtime_command_failed' },
  ]);
});
