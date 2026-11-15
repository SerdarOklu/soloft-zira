import type { Role } from './roles';

/**
 * The six menus plus settings, and who sees each one (PDT section 10.3).
 * The interface hides what a role may not open; the API enforces it.
 */
export type ScreenKey =
  | 'dashboard'
  | 'fields'
  | 'fieldMemory'
  | 'waterVault'
  | 'rotation'
  | 'messages'
  | 'farmer'
  | 'dataCenter'
  | 'settings';

export interface Screen {
  key: ScreenKey;
  href: string;
  roles: readonly Role[];
  /** Development phase in which the screen gets its content (docs/phases.md). */
  phase: number;
  /** Pinned to the foot of the sidebar. */
  bottom?: boolean;
}

const STAFF: readonly Role[] = ['admin', 'agronomist', 'cooperative_user'];

export const SCREENS: readonly Screen[] = [
  { key: 'dashboard', href: '/', roles: STAFF, phase: 3 },
  { key: 'fields', href: '/fields', roles: STAFF, phase: 3 },
  { key: 'fieldMemory', href: '/field-memory', roles: STAFF, phase: 5 },
  { key: 'waterVault', href: '/water-vault', roles: STAFF, phase: 4 },
  { key: 'rotation', href: '/rotation', roles: STAFF, phase: 6 },
  { key: 'messages', href: '/messages', roles: ['admin', 'agronomist'], phase: 6 },
  { key: 'farmer', href: '/farmer', roles: ['farmer'], phase: 7 },
  { key: 'dataCenter', href: '/data-center', roles: ['admin', 'agronomist'], phase: 3 },
  { key: 'settings', href: '/settings', roles: ['admin', 'cooperative_user'], phase: 7, bottom: true },
];

export function screensFor(role: Role): Screen[] {
  return SCREENS.filter((screen) => screen.roles.includes(role));
}

export function canOpen(role: Role, key: ScreenKey): boolean {
  return SCREENS.some((screen) => screen.key === key && screen.roles.includes(role));
}

/** Up to four destinations for the mobile dock, in menu order. */
export function dockScreensFor(role: Role): Screen[] {
  const preferred: ScreenKey[] = ['dashboard', 'fields', 'waterVault', 'rotation', 'farmer'];
  return screensFor(role).filter((screen) => preferred.includes(screen.key));
}
