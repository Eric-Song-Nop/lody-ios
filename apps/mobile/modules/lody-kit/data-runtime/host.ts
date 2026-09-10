// The iOS message shape stays unchanged. Android bounds each synchronous bridge
// call and acknowledges admission before JS sends the next chunk.
type AndroidBridge = {
  postChunk(id: number, index: number, total: number, value: string): boolean;
};
const android = (globalThis as unknown as { lodyDataHost?: AndroidBridge })
  .lodyDataHost;
let sequence = 0;
export function sendToHost(message: object) {
  if (!android) {
    (globalThis as any).webkit.messageHandlers.dataRuntime.postMessage(message);
    return;
  }
  const value = JSON.stringify(message);
  if (value.length > 4 * 1024 * 1024) {
    android.postChunk(
      ++sequence,
      0,
      1,
      JSON.stringify({ type: 'bridgeError', reason: 'bridge_limit' }),
    );
    throw new Error('bridge_limit');
  }
  const size = 32 * 1024;
  const total = Math.max(1, Math.ceil(value.length / size));
  const id = ++sequence;
  for (let index = 0; index < total; index++) {
    if (
      !android.postChunk(
        id,
        index,
        total,
        value.slice(index * size, (index + 1) * size),
      )
    )
      throw new Error('bridge_rejected');
  }
}

if (android) {
  Object.assign(globalThis, {
    async lodyRuntimeInvoke(id: number, method: string, args: unknown[]) {
      try {
        const runtime = (globalThis as any).dataRuntime;
        if (
          !Object.hasOwn(runtime, method) ||
          typeof runtime[method] !== 'function'
        )
          throw new Error('unknown_method');
        const result = await runtime[method](...args);
        sendToHost({ type: 'rpc', id, result: result ?? null });
      } catch {
        // Do not transport exception strings that may contain request data.
        sendToHost({ type: 'rpc', id, error: 'runtime_command_failed' });
      }
    },
  });
}
