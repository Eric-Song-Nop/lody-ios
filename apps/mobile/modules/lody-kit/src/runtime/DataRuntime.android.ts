import { NativeModule, requireNativeModule } from 'expo';

declare class DataRuntimeModule extends NativeModule {
  runDataRuntimeVerification(): Promise<string>;
}

const native = requireNativeModule<DataRuntimeModule>('LodyKit');
export const runDataRuntimeVerification = () =>
  native.runDataRuntimeVerification();
