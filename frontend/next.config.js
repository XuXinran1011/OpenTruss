/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // API 代理配置（如果需要）
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig

