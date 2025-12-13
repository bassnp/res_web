const path = require('path');

const nextConfig = {
  output: 'export',
  outputFileTracingRoot: path.join(__dirname, './'),
  images: {
    unoptimized: true,
  },
  // Static export generates files to 'out' directory by default
  // No trailing slash for cleaner URLs
  trailingSlash: false,
};

module.exports = nextConfig;
