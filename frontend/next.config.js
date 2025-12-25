/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Disable font optimization in CI to avoid network issues
  optimizeFonts: process.env.CI !== 'true',
  // API 代理配置（如果需要）
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/:path*',
      },
    ]
  },
  // 排除e2e测试文件
  pageExtensions: ['tsx', 'ts', 'jsx', 'js'],
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
    }
    return config
  },
}

module.exports = nextConfig

