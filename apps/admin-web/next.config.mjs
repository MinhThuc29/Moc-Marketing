/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@moc-healthy/ui', '@moc-healthy/contracts'],
};

export default nextConfig;
