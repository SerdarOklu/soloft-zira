import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // A self-contained server bundle keeps the production image small on the VPS.
  output: 'standalone',
};

export default nextConfig;
