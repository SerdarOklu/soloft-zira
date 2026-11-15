/**
 * Zira's own decorative artwork for the farmer screens: simple flat shapes, drawn here, not
 * taken from any game or stock set. Every piece is `aria-hidden`; it never carries data.
 */
import type { SVGProps } from 'react';

type Props = SVGProps<SVGSVGElement>;

const base = { 'aria-hidden': true, focusable: false } as const;

/** A water drop. */
export function DropIllustration(props: Props) {
  return (
    <svg viewBox="0 0 64 80" {...base} {...props}>
      <path
        d="M32 4C22 22 8 36 8 54a24 24 0 0 0 48 0C56 36 42 22 32 4Z"
        fill="var(--zf-water)"
      />
      <path
        d="M20 52a12 12 0 0 0 10 12"
        fill="none"
        stroke="#fff"
        strokeWidth="4"
        strokeLinecap="round"
        opacity=".7"
      />
    </svg>
  );
}

/** A seedling in a mound of soil. */
export function SproutIllustration(props: Props) {
  return (
    <svg viewBox="0 0 120 90" {...base} {...props}>
      <ellipse cx="60" cy="74" rx="52" ry="14" fill="var(--zf-soil)" />
      <ellipse cx="60" cy="70" rx="40" ry="9" fill="var(--zf-soil-light)" />
      <path d="M60 70V40" stroke="var(--zf-leaf-dark)" strokeWidth="5" strokeLinecap="round" />
      <path d="M60 46C60 28 44 20 28 24c0 18 14 26 32 22Z" fill="var(--zf-leaf)" />
      <path d="M60 40C60 22 76 12 94 16c0 18-16 28-34 24Z" fill="var(--zf-leaf-dark)" />
    </svg>
  );
}

/** A tilted plot of crop rows, standing for a field (not a picture of it). */
export function FieldIllustration(props: Props) {
  const rows = [0, 1, 2, 3, 4];
  return (
    <svg viewBox="0 0 160 110" {...base} {...props}>
      <path d="M80 100 8 66v14l72 34 72-34V66Z" fill="var(--zf-soil)" />
      <path d="M80 98 8 64 80 30l72 34Z" fill="var(--zf-soil-light)" />
      {rows.map((row) => (
        <path
          key={row}
          d={`M${22 + row * 7} ${68 - row * 3.4}L${94 + row * 7} ${34 + row * 3.4 + 0}`}
          stroke={row % 2 ? 'var(--zf-leaf)' : 'var(--zf-leaf-dark)'}
          strokeWidth="6"
          strokeLinecap="round"
          opacity=".9"
        />
      ))}
    </svg>
  );
}

/** Rolling hills and a sun, for the page banner. It stretches to the width of the banner. */
export function MeadowBanner(props: Props) {
  return (
    <svg viewBox="0 0 600 160" preserveAspectRatio="xMidYMax slice" {...base} {...props}>
      <rect width="600" height="160" fill="var(--zf-sky)" />
      <circle cx="520" cy="42" r="26" fill="var(--zf-sun)" />
      <path d="M0 110C80 70 160 70 250 104s170 20 350-26v108H0Z" fill="var(--zf-leaf-light)" />
      <path d="M0 132C110 96 210 112 320 128s190 8 280-18v50H0Z" fill="var(--zf-leaf)" />
      <path d="M0 150C120 128 230 140 340 150s170 4 260-8v18H0Z" fill="var(--zf-leaf-dark)" />
    </svg>
  );
}
