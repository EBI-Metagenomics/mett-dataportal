// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Custom plugin to handle bgzip files
const bgzipPlugin = () => {
  return {
    name: 'bgzip-handler',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (req.url && (req.url.includes('.fa.gz') || req.url.includes('.gff.gz'))) {
          // Set proper headers for bgzip files
          res.setHeader('Content-Type', 'application/octet-stream');
          res.setHeader('Content-Encoding', 'identity');
        }
        next();
      });
    },
  };
};

export default defineConfig({
  plugins: [react(), bgzipPlugin()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        // Auto-import shared SCSS vars/mixins (optional)
        additionalData: `@use "@/styles/variables.scss" as *;`,
        // Use modern Sass API
        api: 'modern-compiler',
      },
    },
  },
  optimizeDeps: {
    esbuildOptions: {
      loader: {
        '.js': 'jsx',
      },
    },
  },
  server: {
    fs: {
      // Allow serving files from outside the project root
      allow: ['..'],
    },
  },
  publicDir: 'public',
})
