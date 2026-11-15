import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { describe, expect, it } from 'vitest';

import en from '../messages/en.json';
import tr from '../messages/tr.json';

/**
 * The key lists live only in config/ (the backend reads them from there). The screens label
 * them from the message files, so a key added to config/ without a label must fail here.
 */
function topLevelKeys(file: string, section: string): string[] {
  const lines = readFileSync(resolve(__dirname, '../../config', file), 'utf-8').split('\n');
  const start = lines.findIndex((line) => line.trim() === `${section}:`);
  const keys: string[] = [];
  for (const line of lines.slice(start + 1)) {
    if (/^\S/.test(line)) break; // the next top-level block
    const match = /^ {2}([a-z0-9_]+):\s*$/.exec(line);
    if (match) keys.push(match[1]);
  }
  return keys;
}

describe('labels for the lists in config/', () => {
  const soils = topLevelKeys('soils.yaml', 'soils');
  const sources = topLevelKeys('data_sources.yaml', 'sources');

  it('reads the keys it is meant to check', () => {
    expect(soils).toContain('loam');
    expect(sources).toContain('power');
  });

  it.each([
    ['tr', tr],
    ['en', en],
  ])('has a soil label for every soil texture (%s)', (_language, messages) => {
    expect(Object.keys(messages.soils).sort()).toEqual([...soils].sort());
  });

  it.each([
    ['tr', tr],
    ['en', en],
  ])('has a role line for every data source (%s)', (_language, messages) => {
    expect(Object.keys(messages.dataCenter.roles).sort()).toEqual([...sources].sort());
  });
});
