import assert from 'node:assert/strict';
import test from 'node:test';
import generator from '../../plugins/androidLocales.js';

test('Android resources preserve literal XML, whitespace, quotes, slashes and formatting-looking text', () => {
  const catalog = {
    'native.example': ' @name & <tag> "quoted" \\path\nIt\'s 100% {name} ',
  };
  const output = generator.buildAndroidLocales({
    en: catalog,
    'zh-Hans': catalog,
  });
  assert.ok(output.resources.en.includes('formatted="false"'));
  assert.ok(
    output.resources.en.includes(
      '" @name &amp; &lt;tag&gt; \\"quoted\\" \\\\path\\nIt\\\'s 100% {name} "',
    ),
  );
  assert.ok(output.kotlin.includes('setOf("name")'));
});
test('plural siblings collapse into one Android quantity resource', () => {
  const en = {
    'native.files.one': '{count} file',
    'native.files.other': '{count} files',
  };
  const zh = {
    'native.files.one': '{count} 个文件',
    'native.files.other': '{count} 个文件',
  };
  const output = generator.buildAndroidLocales({ en, 'zh-Hans': zh });
  assert.equal(output.count, 1);
  assert.match(output.resources.en, /<plurals name="lody_native_files">/);
  assert.match(output.resources.en, /quantity="other">"\{count\} files"/);
  assert.match(output.kotlin, /R.plurals.lody_native_files, true/);
  assert.throws(
    () =>
      generator.buildAndroidLocales({
        en,
        'zh-Hans': { 'native.files.one': 'one' },
      }),
    /Missing/,
  );
});
test('colliding Android resource names fail instead of silently replacing strings', () => {
  assert.throws(
    () =>
      generator.buildAndroidLocales({
        en: { 'native.Foo': 'a', 'native.foo': 'b' },
      }),
    /collision/,
  );
});
