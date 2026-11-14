import type { NextConfig } from 'next';
import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin('./i18n/request.ts');

const nextConfig: NextConfig = {
  // A self-contained server bundle keeps the production image small on the VPS.
  output: 'standalone',
};

export default withNextIntl(nextConfig);
