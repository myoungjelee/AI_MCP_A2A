/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  env: {
    // API Endpoints
    NEXT_PUBLIC_ANALYZE_ENDPOINT: "/analyze",
    NEXT_PUBLIC_STREAM_ENDPOINT: "/analyze/stream",
    NEXT_PUBLIC_HEALTH_ENDPOINT: "/health",
    NEXT_PUBLIC_MCP_STATUS_ENDPOINT: "/mcp/status",
    NEXT_PUBLIC_VALIDATE_ENDPOINT: "/validate/investment/json",
  },
};

module.exports = nextConfig;
