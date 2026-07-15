import type { NextConfig } from "next";

// All /api/* requests are proxied to the FastAPI backend, so the browser only
// ever talks to the Next.js origin and the backend needs no CORS setup.
const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND_URL}/:path*`,
      },
    ];
  },
};

export default nextConfig;
