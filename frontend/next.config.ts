import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow connecting to dev server via network IPs
  allowedDevOrigins: ["127.0.0.1", "192.168.0.127"],
};

export default nextConfig;
