import { notFound } from 'next/navigation';

// Any unknown address under a locale shows the localized not-found page.
export default function CatchAll() {
  notFound();
}
