import type { ReactNode } from 'react';

// Zira has no logo artwork yet. These text marks fill the brand slots of the shell
// and the sign-in screen until it does; swap them for <img> elements then.

export function Wordmark({ name }: { name: string }): ReactNode {
  return <span className="zira-wordmark">{name}</span>;
}

export function WordmarkIcon({ name }: { name: string }): ReactNode {
  return (
    <span className="zira-wordmark zira-wordmark--icon" aria-hidden="true">
      {name.charAt(0)}
    </span>
  );
}
