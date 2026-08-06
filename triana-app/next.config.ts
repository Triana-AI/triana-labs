import type { NextConfig } from "next";

const backendOrigin = (process.env.TRIANA_BACKEND_API_ORIGIN ?? "http://127.0.0.1:8000").replace(/\/$/, "");

const nextConfig: NextConfig = {
  poweredByHeader: false,
  images: { unoptimized: true },
  async rewrites() {
    return [{
      source: "/api/v1/:path*",
      destination: `${backendOrigin}/api/v1/:path*`,
    }];
  },
};

export default nextConfig;
