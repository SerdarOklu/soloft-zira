import { describe, expect, it } from 'vitest';

import en from '../messages/en.json';
import tr from '../messages/tr.json';
import { canOpen, dockScreensFor, SCREENS, screensFor } from './nav';
import { ROLES } from './roles';

const keys = (role: Parameters<typeof screensFor>[0]) => screensFor(role).map((s) => s.key);

describe('menu per role (PDT section 10.3)', () => {
  it('shows an admin every screen', () => {
    expect(keys('admin')).toEqual(SCREENS.map((s) => s.key));
  });

  it('hides user management from an agronomist', () => {
    expect(keys('agronomist')).toContain('dataCenter');
    expect(keys('agronomist')).not.toContain('settings');
  });

  it('hides the Data Center from a cooperative user', () => {
    expect(keys('cooperative_user')).not.toContain('dataCenter');
    expect(keys('cooperative_user')).toContain('settings');
    expect(canOpen('cooperative_user', 'dataCenter')).toBe(false);
  });

  it('gives a farmer no console screen until the farmer view exists', () => {
    expect(keys('farmer')).toEqual([]);
  });

  it('keeps the dock to at most four destinations', () => {
    for (const role of ROLES) expect(dockScreensFor(role).length).toBeLessThanOrEqual(4);
  });
});

describe('translations', () => {
  const shape = (value: unknown, path = ''): string[] =>
    value !== null && typeof value === 'object' && !Array.isArray(value)
      ? Object.entries(value).flatMap(([key, child]) => shape(child, `${path}${key}.`))
      : [path + (Array.isArray(value) ? `[${value.length}]` : '')];

  it('has the same keys in Turkish and English', () => {
    expect(shape(tr).sort()).toEqual(shape(en).sort());
  });

  it('names every screen, role and dock destination in both languages', () => {
    for (const messages of [tr, en]) {
      for (const screen of SCREENS) {
        expect(messages.nav[screen.key]).toBeTruthy();
        expect(messages.screens[screen.key].title).toBeTruthy();
        expect(messages.screens[screen.key].items.length).toBeGreaterThan(0);
      }
      for (const role of ROLES) expect(messages.roles[role]).toBeTruthy();
      for (const screen of dockScreensFor('admin')) {
        expect(messages.dock[screen.key as keyof typeof messages.dock]).toBeTruthy();
      }
    }
  });
});
