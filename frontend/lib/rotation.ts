/** The rotations the user can pick from until Field Memory reads them from satellite history. */
export const ROTATION_PRESETS = {
  wheatFallow: 'winter_wheat,fallow',
  wheatEvery: 'winter_wheat',
  wheatLentil: 'winter_wheat,lentil',
  history: 'history',
} as const;
