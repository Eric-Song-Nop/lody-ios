import { homeVerify } from '@/screens/debug/HomePreviewScreen';
import { uiVerify } from '@/screens/debug/uiVerify';
import { InboxScreen } from '@/screens/InboxScreen';
import { Redirect } from 'expo-router';
function DebugRedirect() {
  return <Redirect href="/debug" />;
}
export default uiVerify && !homeVerify ? DebugRedirect : InboxScreen.Route;
