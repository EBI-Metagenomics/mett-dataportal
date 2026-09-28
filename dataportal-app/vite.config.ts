// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

// JBrowse reads bgzip itself. If the dev server marks these responses as
// Content-Encoding: gzip, Chrome decodes them first and fails on a
// multi-member bgzip stream (net::ERR_CONTENT_DECODING_FAILED).
// .fna.gz is the 20hm assembly suffix; .fa.gz does not match it.
const blockGzipPath = (url = '') =>
  /\.(?:fa|fna|fasta|gff)\.gz(?:$|[.?#])/i.test(url.split('?')[0]);

const bgzipPlugin = () => {
  return {
    name: 'bgzip-handler',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (req.url && blockGzipPath(req.url)) {
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

