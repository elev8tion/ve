import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      // VisualEssential CDN — outfit and scene thumbnails
      { protocol: 'https', hostname: 'lugfcahmpvajonmzhqcd.supabase.co' },
    ],
  },
};

export default nextConfig;
