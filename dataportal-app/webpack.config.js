// eslint-disable-next-line @typescript-eslint/no-require-imports
const ESLintPlugin = require('eslint-webpack-plugin');

// eslint-disable-next-line no-undef
module.exports = {
  // Other Webpack configurations
  plugins: [
    new ESLintPlugin({
      emitWarning: true, // Show warnings without breaking the build
      failOnError: false, // Prevent build failure on ESLint errors
    }),
  ],
};
