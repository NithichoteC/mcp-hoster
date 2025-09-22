/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  // API proxy for development
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL + '/api/:path*',
      },
      {
        source: '/auth/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL + '/auth/:path*',
      },
      {
        source: '/mcp/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL + '/mcp/:path*',
      },
    ];
  },

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
  },

  // Enable standalone output for Docker
  output: 'standalone',

  // Disable x-powered-by header
  poweredByHeader: false,

  // Compression
  compress: true,

  // Image optimization
  images: {
    domains: ['github.com', 'avatars.githubusercontent.com'],
  },
};

module.exports = nextConfig;