import { requireNativeView } from 'expo';
import { createElement, type ComponentType } from 'react';
import type {
  NativeGroupedListProps as FullProps,
  NativeListRow as FullRow,
  NativeListSection as FullSection,
} from './NativeGroupedList';

// Expand this contract only with a real native implementation and host checks.
export type NativeListRow = Pick<
  FullRow,
  | 'id'
  | 'title'
  | 'subtitle'
  | 'subtitleMono'
  | 'value'
  | 'image'
  | 'action'
  | 'navigates'
  | 'disclosure'
  | 'destructive'
>;
export type NativeListSection = Pick<
  FullSection,
  'id' | 'header' | 'footer'
> & {
  rows: NativeListRow[];
};
export type NativeGroupedListProps = Omit<
  FullProps,
  | 'sections'
  | 'segments'
  | 'segmentsUseSearchScope'
  | 'selectedSegment'
  | 'onSegmentChange'
  | 'contentStyle'
  | 'onRowAction'
  | 'previewUserId'
  | 'previewWorkspaceId'
> & { sections: NativeListSection[] };
const rowKeys = new Set([
  'id',
  'title',
  'subtitle',
  'subtitleMono',
  'value',
  'image',
  'action',
  'navigates',
  'disclosure',
  'destructive',
]);
const sectionKeys = new Set(['id', 'header', 'footer', 'rows']);
const unsupportedProps = [
  'segments',
  'segmentsUseSearchScope',
  'selectedSegment',
  'onSegmentChange',
  'contentStyle',
  'onRowAction',
  'previewUserId',
  'previewWorkspaceId',
];
const NativeView = requireNativeView(
  'LodyKit',
  'LodyGroupedList',
) as ComponentType<NativeGroupedListProps & { refreshEnabled: boolean }>;

export function NativeGroupedList({
  onRefresh,
  ...props
}: NativeGroupedListProps) {
  for (const key of unsupportedProps) {
    if (key in props)
      throw new Error(`Android grouped list does not implement ${key}`);
  }
  for (const section of props.sections) {
    for (const key of Object.keys(section)) {
      if (!sectionKeys.has(key))
        throw new Error(`Android list section does not implement ${key}`);
    }
    for (const row of section.rows) {
      for (const key of Object.keys(row)) {
        if (!rowKeys.has(key))
          throw new Error(`Android list row does not implement ${key}`);
      }
    }
  }
  return createElement(NativeView, {
    ...props,
    onRefresh,
    refreshEnabled: !!onRefresh,
  });
}
