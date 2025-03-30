import { defineConfig } from 'vite';
import { resolve } from 'path';
import reactSWC from '@vitejs/plugin-react-swc';

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [reactSWC()],
    resolve: {
        alias: {
            '@': resolve(__dirname, './src')
        }
    },
    optimizeDeps: {
        exclude: ['lucide-react']
    },
    server: {
        port: 3000,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true
            }
        }
    },
    build: {
        outDir: 'dist',
        sourcemap: true,
        rollupOptions: {
            output: {
                manualChunks: {
                    vendor: ['react', 'react-dom', 'react-router-dom'],
                    ui: ['antd', 'lucide-react']
                }
            }
        }
    }
}); 