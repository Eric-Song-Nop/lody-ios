import assert from 'node:assert/strict';
import test from 'node:test';
import { build } from 'esbuild';

const bundle = await build({
  entryPoints: [
    new URL(
      '../../modules/lody-kit/src/list/NativeGroupedList.tsx',
      import.meta.url,
    ).pathname,
  ],
  bundle: true,
  format: 'esm',
  platform: 'node',
  write: false,
  plugins: [
    {
      name: 'native-view',
      setup(builder) {
        builder.onResolve({ filter: /^(expo|react)$/ }, ({ path }) => ({
          path,
          namespace: 'mock',
        }));
        builder.onLoad({ filter: /.*/, namespace: 'mock' }, ({ path }) => ({
          contents: {
            expo: 'export function requireNativeView() { return (props) => props; }',
            react:
              'export function createElement(type, props) { return type(props); }',
          }[path],
        }));
      },
    },
  ],
});

const source = bundle.outputFiles[0].text;
const module = await import(
  `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`
);

test('grouped lists install pull-to-refresh only when they have a refresh handler', () => {
  const required = { sections: [], onRowPress() {} };
  assert.equal(module.NativeGroupedList(required).refreshEnabled, false);

  const onRefresh = () => {};
  const refreshable = module.NativeGroupedList({ ...required, onRefresh });
  assert.equal(refreshable.refreshEnabled, true);
  assert.equal(refreshable.onRefresh, onRefresh);
});
