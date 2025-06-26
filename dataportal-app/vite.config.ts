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

// Custom plugin to handle JBrowse worker files
const jbrowseWorkerPlugin = () => {
  return {
    name: 'jbrowse-worker-handler',
    load(id) {
      if (id.includes('makeWorkerInstance.js')) {
        // Return a simple module that doesn't cause IIFE issues
        return `
          export default function makeWorkerInstance() {
            return null;
          }
        `;
      }
    },
  };
};

export default defineConfig({
  plugins: [react(), bgzipPlugin(), jbrowseWorkerPlugin()],
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
      },
    },
  },
  optimizeDeps: {
    esbuildOptions: {
      loader: {
        '.js': 'jsx',
      },
    },
    include: [
      'react',
      'react-dom',
      '@jbrowse/core',
      '@jbrowse/plugin-linear-genome-view',
      '@jbrowse/product-core',
      '@jbrowse/react-app2',
      '@jbrowse/sv-core',
    ],
  },
  build: {
    target: 'es2015',
    minify: 'esbuild',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          jbrowse: [
            '@jbrowse/core',
            '@jbrowse/plugin-linear-genome-view',
            '@jbrowse/product-core',
            '@jbrowse/react-app2',
            '@jbrowse/sv-core',
          ],
        },
      },
      external: [],
    },
    commonjsOptions: {
      include: [/node_modules/],
      transformMixedEsModules: true,
    },
    chunkSizeWarningLimit: 1000,
  },
  define: {
    global: 'globalThis',
  },
  server: {
    fs: {
      // Allow serving files from outside the project root
      allow: ['..'],
    },
  },
  publicDir: 'public',
})
