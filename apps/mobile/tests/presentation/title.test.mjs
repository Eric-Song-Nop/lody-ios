import assert from 'node:assert/strict';
import test from 'node:test';
import { setLocale, translationsFor } from '../../src/lib/i18n/index.ts';
import { resolvePageTitle } from '../../src/lib/presentation/title.ts';

test('page titles resolve in the render snapshot without changing literal user titles', () => {
  const pageTitle = (t) => t('tabs.settings');
  const english = translationsFor('en');
  const chinese = translationsFor('zh-Hans');
  try {
    setLocale('zh-Hans');
    assert.equal(resolvePageTitle(pageTitle, english.t), 'Settings');
    assert.equal(resolvePageTitle(pageTitle, chinese.t), '设置');
    assert.equal(resolvePageTitle(pageTitle), '设置');
    assert.equal(
      resolvePageTitle('My 设置 {workspace}', chinese.t),
      'My 设置 {workspace}',
    );
    setLocale('en');
    assert.equal(resolvePageTitle(pageTitle), 'Settings');
    assert.equal(resolvePageTitle(pageTitle, chinese.t), '设置');
  } finally {
    setLocale('en');
  }
});
