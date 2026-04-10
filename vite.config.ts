import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  
  root: './',
  publicDir: 'public',
  
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@app': path.resolve(__dirname, './src/app'),
      '@components': path.resolve(__dirname, './src/app/components')
    }
  },
  
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: false,
    minify: 'esbuild',
    target: 'esnext',
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom']
        }
      }
    }
  },
  
  server: {
    port: 5173,
    strictPort: true,
    host: 'localhost',
    open: false
  },
  
  clearScreen: false,
  
  envPrefix: ['VITE_', 'TAURI_'],
  
  optimizeDeps: {
    include: ['react', 'react-dom']
  }
});
