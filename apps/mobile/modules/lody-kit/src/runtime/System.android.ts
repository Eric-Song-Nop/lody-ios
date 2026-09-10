import { NativeModule, requireNativeModule } from 'expo';

declare class AndroidSystem extends NativeModule {
  readonly initialInboxView: number;
  saveInboxView(index: number): void;
  readInboxExpansion(): Record<string, boolean>;
  saveInboxExpansion(projectId: string, expanded: boolean): void;
  copyText(text: string): void;
  selectionFeedback(): Promise<void>;
}
const native = requireNativeModule<AndroidSystem>('LodyKit');
export const initialInboxView = native.initialInboxView;
export const saveInboxView = (index: number) => native.saveInboxView(index);
export const readInboxExpansion = () => native.readInboxExpansion();
export const saveInboxExpansion = (projectId: string, expanded: boolean) =>
  native.saveInboxExpansion(projectId, expanded);
export const copyText = (text: string) => native.copyText(text);
export const selectionFeedback = () => native.selectionFeedback();
