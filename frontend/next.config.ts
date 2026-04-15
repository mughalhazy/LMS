import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Skip type-checking and lint during `next build` — Render free tier OOMs on tsc.
  // Types are still enforced in the editor and CI.
  typescript: { ignoreBuildErrors: true },
  eslint: { ignoreDuringBuilds: true },
};

export default nextConfig;
