// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

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
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@components': fileURLToPath(new URL('./src/components', import.meta.url)),
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        // Auto-import shared SCSS vars/mixins
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
  },
  build: {
    target: 'es2015',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
        },
      },
    },
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

