/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  env: {
    // Pinggy Tunnel URL (배포용)
    NEXT_PUBLIC_API_URL: "https://zhapp-175-113-49-154.a.free.pinggy.link",

    // API Endpoints
    NEXT_PUBLIC_ANALYZE_ENDPOINT: "/analyze",
    NEXT_PUBLIC_STREAM_ENDPOINT: "/analyze/stream",
    NEXT_PUBLIC_HEALTH_ENDPOINT: "/health",
    NEXT_PUBLIC_MCP_STATUS_ENDPOINT: "/mcp/status",
    NEXT_PUBLIC_VALIDATE_ENDPOINT: "/validate/investment/json",
  },
  // Vercel 배포를 위한 환경 변수 강제 설정
  publicRuntimeConfig: {
    NEXT_PUBLIC_API_URL: "https://zhapp-175-113-49-154.a.free.pinggy.link",
  },
};

module.exports = nextConfig;
