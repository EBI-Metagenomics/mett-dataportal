// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
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
    middlewareMode: true,
  },
  publicDir: 'public',
})
