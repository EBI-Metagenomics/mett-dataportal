// craco.config.js
const path = require('path');

module.exports = {
  webpack: {
    alias: {
      '@components': path.resolve(__dirname, 'src/components/'),
      // Add other aliases or custom configurations here
    },
    configure: (webpackConfig, { env, paths }) => {
      // You can modify the `webpackConfig` directly here
      return webpackConfig;
    },
  },
};
