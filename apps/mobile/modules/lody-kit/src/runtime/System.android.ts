import { NativeModule, requireNativeModule } from 'expo';

export type ToastKind = 'info' | 'warning' | 'error';
export type SessionBannerKind = 'completed' | 'attention';

declare class AndroidSystem extends NativeModule {
  readonly initialInboxView: number;
  saveInboxView(index: number): void;
  readInboxExpansion(): Record<string, boolean>;
  saveInboxExpansion(projectId: string, expanded: boolean): void;
  copyText(text: string): void;
  selectionFeedback(): Promise<void>;
  showToast(message: string, kind: ToastKind): void;
  showSessionBanner(title: string, kind: SessionBannerKind): void;
  dismissSessionBanner(): void;
}
const native = requireNativeModule<AndroidSystem>('LodyKit');
export const initialInboxView = native.initialInboxView;
export const saveInboxView = (index: number) => native.saveInboxView(index);
export const readInboxExpansion = () => native.readInboxExpansion();
export const saveInboxExpansion = (projectId: string, expanded: boolean) =>
  native.saveInboxExpansion(projectId, expanded);
export const copyText = (text: string) => native.copyText(text);
export const selectionFeedback = () => native.selectionFeedback();
export const showToast = (message: string, kind: ToastKind = 'error') =>
  native.showToast(message, kind);
export const showSessionBanner = (title: string, kind: SessionBannerKind) =>
  native.showSessionBanner(title, kind);
export const dismissSessionBanner = () => native.dismissSessionBanner();
