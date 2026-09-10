import { NativeModule, requireNativeModule } from 'expo';

declare class StorageModule extends NativeModule {
  readAuthToken(): Promise<string | null>;
  saveAuthToken(token: string): Promise<void>;
  clearAuthToken(): Promise<void>;
  readLocalStartup(): Promise<Record<string, string>>;
  readLocalValue(key: string): Promise<string | null>;
  writeLocalValue(key: string, value: string): Promise<void>;
  clearLocalValues(): Promise<void>;
  runStorageVerification(): Promise<string>;
}
const native = requireNativeModule<StorageModule>('LodyKit');
export const readAuthToken = () => native.readAuthToken();
export const saveAuthToken = (token: string) => native.saveAuthToken(token);
export const clearAuthToken = () => native.clearAuthToken();
export const readLocalStartup = () => native.readLocalStartup();
export const readLocalValue = (key: string) => native.readLocalValue(key);
export const writeLocalValue = (key: string, value: string) =>
  native.writeLocalValue(key, value);
export const clearLocalValues = () => native.clearLocalValues();
export const runStorageVerification = () => native.runStorageVerification();
