import type { ReactNode } from 'react';

// Zira artwork (public/brand). Names say what the artwork sits on: the "-light" files are the
// pale version for dark surfaces, the "-dark" files the dark version for light surfaces.
// The navigation chrome is dark in both themes, so it always takes the pale version; the sign-in
// screen follows the page theme.

/* eslint-disable @next/next/no-img-element */

export function Wordmark({ name }: { name: string }): ReactNode {
  return <img className="zira-logo" src="/brand/zira-logo-light.png" alt={name} />;
}

export function WordmarkIcon({ name }: { name: string }): ReactNode {
  return <img className="zira-logo zira-logo--icon" src="/brand/zira-icon-light.png" alt={name} />;
}

export function AuthLogo({ name }: { name: string }): ReactNode {
  return (
    <span className="zira-auth-logo">
      <img
        className="zira-logo zira-logo--auth zira-logo--on-light"
        src="/brand/zira-logo-dark.png"
        alt={name}
      />
      <img
        className="zira-logo zira-logo--auth zira-logo--on-dark"
        src="/brand/zira-logo-light.png"
        alt=""
        aria-hidden="true"
      />
    </span>
  );
}
