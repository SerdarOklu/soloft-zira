import createMiddleware from 'next-intl/middleware';

import { routing } from './i18n/routing';

// Adds the locale prefix and negotiates the language. API routes, Next.js internals
// and files with an extension are left alone.
export default createMiddleware(routing);

export const config = {
  matcher: '/((?!api|_next|_vercel|.*\\..*).*)',
};
