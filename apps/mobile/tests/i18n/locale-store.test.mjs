import assert from 'node:assert/strict';
import test from 'node:test';
import {
  currentLocale,
  setLocale,
  subscribeLocale,
  t,
  tp,
  translationsFor,
} from '../../src/lib/i18n/index.ts';

test('locale observers read updated copy, suppress duplicates and unsubscribe', () => {
  setLocale('en');
  const observed = [];
  const stop = subscribeLocale(() => {
    observed.push({ locale: currentLocale(), close: t('native.close') });
  });
  try {
    setLocale('zh-Hans');
    setLocale('zh-Hans');
    setLocale('en');
    assert.deepEqual(observed, [
      { locale: 'zh-Hans', close: '关闭' },
      { locale: 'en', close: 'Close' },
    ]);
    stop();
    setLocale('zh-Hans');
    assert.equal(observed.length, 2);
  } finally {
    stop();
    setLocale('en');
  }
});

test('render snapshots retain their language while imperative copy follows the current locale', () => {
  setLocale('en');
  const english = translationsFor('en');
  const chinese = translationsFor('zh-Hans');
  try {
    setLocale('zh-Hans');
    assert.equal(english.t('native.close'), 'Close');
    assert.equal(chinese.t('native.close'), '关闭');
    assert.equal(t('native.close'), '关闭');
    assert.equal(
      english.tp('settings.machineCount', 1, { count: 1 }),
      '1 computer',
    );
    assert.equal(tp('settings.machineCount', 1, { count: 1 }), '1 台电脑');
    setLocale('en');
    assert.equal(
      chinese.tp('settings.machineCount', 2, { count: 2 }),
      '2 台电脑',
    );
    assert.equal(tp('settings.machineCount', 2, { count: 2 }), '2 computers');
  } finally {
    setLocale('en');
  }
});
