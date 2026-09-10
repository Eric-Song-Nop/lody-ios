import { useTranslations } from '@/lib/i18n/useTranslations';
import { useEffect } from 'react';
import { Alert } from 'react-native';
import { NativeGroupedList } from '@lody-ios/kit';
import { definePage } from '@/lib/presentation';
import { useAuth } from '@/cloud/auth/AuthProvider';
import { usePalette } from '@/lib/theme/palette';
import { usePageRuntime } from '@/hooks/screens/usePageRuntime';
import { t } from '../lib/i18n/index.ts';
function View() {
  const { t } = useTranslations();
  const auth = useAuth();
  const colors = usePalette();
  const { cancel } = usePageRuntime();
  useEffect(() => {
    if (!auth.account) cancel();
  }, [auth.account, cancel]);
  return (
    <>
      <NativeGroupedList
        style={{ flex: 1 }}
        accent={colors.accent}
        placeholder={t('account.placeholder')}
        sections={
          auth.account
            ? [
                {
                  id: 'account',
                  rows: [
                    {
                      id: 'name',
                      title: auth.account.user.name,
                      subtitle: auth.account.user.email,
                      image: auth.account.user.image ?? 'person.crop.circle',
                    },
                  ],
                },
                {
                  id: 'logout',
                  footer: auth.error ?? undefined,
                  rows: [
                    {
                      id: 'logout',
                      title: t(
                        auth.busy ? 'account.signingOut' : 'account.signOut',
                      ),
                      destructive: true,
                      action: !auth.busy,
                    },
                  ],
                },
              ]
            : []
        }
        onRowPress={() =>
          Alert.alert(
            t('account.signOutConfirm.title'),
            t('account.signOutConfirm.message'),
            [
              { text: t('common.cancel'), style: 'cancel' },
              {
                text: t('account.signOut'),
                style: 'destructive',
                onPress: () => {
                  void auth.logout();
                },
              },
            ],
          )
        }
      />
    </>
  );
}
export const AccountScreen = definePage({
  id: 'account',
  title: (t) => t('account.title'),
  Component: View,
  presentation: { style: 'push', headerVariant: 'transparent' },
});
