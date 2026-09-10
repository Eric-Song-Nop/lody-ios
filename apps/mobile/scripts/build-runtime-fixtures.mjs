import { Flock } from '@loro-dev/flock-wasm/base64';
import { LoroDoc } from 'loro-crdt/base64';
import { build } from 'esbuild';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { decompress } from 'fzstd';

export async function buildRuntimeFixtures(root, output) {
  const directory = output + '/verification';
  await mkdir(directory, { recursive: true });
  const compiled = await build({
    stdin: {
      contents: `export { projectRows } from './src/cloud/catalog/model.ts';`,
      resolveDir: root,
      loader: 'ts',
    },
    bundle: true,
    format: 'esm',
    platform: 'node',
    write: false,
  });
  const { projectRows } = await import(
    `data:text/javascript;base64,${Buffer.from(compiled.outputFiles[0].text).toString('base64')}`
  );
  const frame = (bytes) => {
    const result = Buffer.alloc(bytes.length + 4);
    result.writeUInt32BE(bytes.length);
    result.set(bytes, 4);
    return result;
  };
  const multipart = (parts) =>
    Buffer.concat(
      parts
        .flatMap((body) => [
          Buffer.from(
            '--lody-fixture\r\nContent-Type: application/octet-stream\r\n\r\n',
          ),
          Buffer.from(body),
          Buffer.from('\r\n'),
        ])
        .concat(Buffer.from('--lody-fixture--\r\n')),
    );
  const manifest = {
    version: 'runtime-v1',
    runtimeSha256: createHash('sha256')
      .update(await readFile(output + '/DataRuntime.html'))
      .digest('hex'),
    cases: [],
    assets: {},
  };
  const save = async (name, bytes) => {
    await writeFile(directory + '/' + name, bytes);
    manifest.assets[name] = createHash('sha256').update(bytes).digest('hex');
    return name;
  };
  const catalog = new Flock('fixture-server');
  catalog.set(['e', 'session-s1'], true, 1);
  catalog.set(
    ['m', 'session-s1'],
    { title: 'Before', machineId: 'fixture-machine' },
    2,
  );
  const snapshot = catalog.exportFile();
  const before = projectRows(catalog.scan(), 'meta');
  const version = catalog.version();
  catalog.set(['m', 'session-s1', 'title'], 'After 👩🏽‍💻 中文', 3);
  const increment = frame(
    Buffer.from(JSON.stringify(catalog.exportJson(version))),
  );
  const normal = {
    name: 'increment',
    expected: [before, projectRows(catalog.scan(), 'meta')],
    bootstrap: await save('increment-bootstrap.bin', multipart([snapshot])),
    update: await save('increment-update.bin', increment),
  };
  manifest.cases.push(normal);
  const compressedFixture = JSON.parse(
    await readFile(
      root + 'verification/android/fixtures/compressed-catalog.json',
      'utf8',
    ),
  );
  const compressed = Buffer.from(compressedFixture.zstdBase64, 'base64');
  const restored = new Flock('compressed-baseline');
  restored.importFile(decompress(compressed));
  manifest.cases.push({
    name: 'compressed',
    expected: [projectRows(restored.scan(), 'meta')],
    bootstrap: await save('compressed-bootstrap.bin', multipart([compressed])),
  });
  const large = new Flock('fixture-large');
  for (let index = 0; index < 800; index++) {
    large.set(['e', `session-${index}`], true, index * 2 + 1);
    large.set(
      ['m', `session-${index}`],
      {
        title: `Session ${index} ${'长文本👩🏽‍💻'.repeat(12)}`,
        machineId: 'fixture-machine',
      },
      index * 2 + 2,
    );
  }
  manifest.cases.push({
    name: 'large',
    expected: [projectRows(large.scan(), 'meta')],
    bootstrap: await save(
      'large-bootstrap.bin',
      multipart([large.exportFile()]),
    ),
  });
  const oversized = new Flock('fixture-output-limit');
  oversized.set(['e', 'session-output-limit'], true, 1);
  oversized.set(
    ['m', 'session-output-limit'],
    { title: 'x'.repeat(4 * 1024 * 1024), machineId: 'fixture-machine' },
    2,
  );
  const oversizedSnapshot = oversized.exportFile();
  if (oversizedSnapshot.length > 8 * 1024 * 1024)
    throw new Error(
      'Output-limit fixture unexpectedly exceeds catalog input ceiling',
    );
  manifest.cases.push({
    name: 'output-limit',
    hostError: 'bridge_limit',
    bootstrap: await save('output-limit.bin', multipart([oversizedSnapshot])),
  });
  for (const [name, update] of [
    ['truncated-length', Buffer.from([0, 0, 1])],
    ['truncated-body', Buffer.from([0, 0, 0, 8, 123])],
    ['invalid-json', frame(Buffer.from('invalid'))],
  ]) {
    manifest.cases.push({
      name,
      error: 'network_or_auth',
      bootstrap: await save(name + '.bin', multipart([snapshot, update])),
    });
  }
  manifest.cases.push({
    name: 'over-limit',
    error: 'catalog_limit',
    bootstrap: await save(
      'over-limit.bin',
      multipart([Buffer.alloc(8 * 1024 * 1024 + 1)]),
    ),
  });
  const history = new LoroDoc();
  history.setPeerId('42');
  history.getList('history').push({
    id: 'reply',
    role: 'assistant',
    finished: true,
    items: [{ type: 'text', text: 'Real Loro WASM 回复' }],
  });
  history.commit();
  manifest.history = await save(
    'history-bootstrap.bin',
    multipart([history.export({ mode: 'snapshot' })]),
  );
  await writeFile(directory + '/manifest.json', JSON.stringify(manifest));
}
