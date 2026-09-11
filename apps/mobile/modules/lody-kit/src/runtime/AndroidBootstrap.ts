import { NativeModule, requireNativeModule } from 'expo';
import type { RuntimeInfo } from './LodyKit';

declare class AndroidBootstrap extends NativeModule<{
  onAppActive: () => void;
}> {
  runLocaleVerification(): Promise<string>;
  readonly runtimeInfo: RuntimeInfo;
}

const native = requireNativeModule<AndroidBootstrap>('LodyKit');
export const runtimeInfo = native.runtimeInfo;
export const addAppActiveListener = (listener: () => void) =>
  native.addListener('onAppActive', listener);

export const runLocaleVerification = () => native.runLocaleVerification();
