const nextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
  // Static export generates files to 'out' directory by default
  // No trailing slash for cleaner URLs
  trailingSlash: false,
};

module.exports = nextConfig;
