const fs = require('fs');
const path = require('path');
const { readCatalogs, PLACEHOLDER } = require('./locales');

function resourceName(key) {
  if (!/^native\.[A-Za-z0-9.]+$/.test(key))
    throw new Error(`Invalid native locale key: ${key}`);
  return `lody_${key.replaceAll('.', '_').toLowerCase()}`;
}
function xmlText(value) {
  // Android quoted strings preserve whitespace and prevent leading @/? references.
  const escaped = value
    .replaceAll('\\', '\\\\')
    .replaceAll('"', '\\"')
    .replaceAll("'", "\\'")
    .replaceAll('\n', '\\n')
    .replaceAll('\r', '\\u000d')
    .replaceAll('\t', '\\t')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;');
  return `"${escaped}"`;
}
function buildAndroidLocales(catalogs) {
  const entries = Object.keys(catalogs.en)
    .filter((key) => key.startsWith('native.') && !key.endsWith('.other'))
    .sort()
    .map((key) => {
      const plural = key.endsWith('.one');
      const base = plural ? key.slice(0, -4) : key;
      const parameters = [
        ...new Set(
          [...catalogs.en[key].matchAll(PLACEHOLDER)].map((match) => match[1]),
        ),
      ].sort();
      return {
        key: base,
        source: key,
        name: resourceName(base),
        plural,
        parameters,
      };
    });
  if (new Set(entries.map((entry) => entry.name)).size !== entries.length)
    throw new Error('Android locale resource name collision');
  const resources = {};
  for (const [locale, catalog] of Object.entries(catalogs)) {
    const lines = [
      '<?xml version="1.0" encoding="utf-8"?>',
      '<!-- Generated from locales; edit the JSON catalogs. -->',
      '<resources>',
    ];
    for (const entry of entries) {
      if (entry.plural) {
        lines.push(`  <plurals name="${entry.name}">`);
        for (const quantity of ['one', 'other']) {
          const value = catalog[`${entry.key}.${quantity}`];
          if (typeof value !== 'string')
            throw new Error(`Missing ${locale}: ${entry.key}.${quantity}`);
          lines.push(
            `    <item quantity="${quantity}">${xmlText(value)}</item>`,
          );
        }
        lines.push('  </plurals>');
      } else {
        const value = catalog[entry.key];
        if (typeof value !== 'string')
          throw new Error(`Missing ${locale}: ${entry.key}`);
        lines.push(
          `  <string name="${entry.name}" formatted="false">${xmlText(value)}</string>`,
        );
      }
    }
    resources[locale] = `${lines.join('\n')}\n</resources>\n`;
  }
  const kotlin = [
    '// Generated from locales; edit the JSON catalogs.',
    'package app.innei.lody.kit.locale',
    '',
    'import app.innei.lody.kit.R',
    '',
    'internal data class StringEntry(val id: Int, val plural: Boolean, val parameters: Set<String>)',
    'internal val lodyStringEntries = mapOf(',
    ...entries.map(
      (entry) =>
        `  "${entry.key}" to StringEntry(R.${entry.plural ? 'plurals' : 'string'}.${entry.name}, ${entry.plural}, setOf(${entry.parameters.map((name) => `"${name}"`).join(', ')})),`,
    ),
    ')',
    '',
  ].join('\n');
  return { resources, kotlin, count: entries.length };
}
function writeAndroidLocales(projectRoot, check = false) {
  const errors = [];
  const catalogs = readCatalogs(projectRoot, (error) => errors.push(error));
  if (errors.length) throw new Error(errors.join('\n'));
  const generated = buildAndroidLocales(catalogs);
  const base = path.join(projectRoot, 'modules/lody-kit/android/src/main');
  const files = new Map([
    [path.join(base, 'res/values/lody_strings.xml'), generated.resources.en],
    [
      path.join(base, 'res/values-b+zh+Hans/lody_strings.xml'),
      generated.resources['zh-Hans'],
    ],
    [
      path.join(base, 'java/app/innei/lody/kit/locale/LodyStringEntries.kt'),
      generated.kotlin,
    ],
  ]);
  for (const [file, content] of files) {
    if (check) {
      if (!fs.existsSync(file) || fs.readFileSync(file, 'utf8') !== content)
        throw new Error(`Stale generated locale resource: ${file}`);
    } else {
      fs.mkdirSync(path.dirname(file), { recursive: true });
      fs.writeFileSync(file, content);
    }
  }
  return generated.count;
}
module.exports = { buildAndroidLocales, writeAndroidLocales };
