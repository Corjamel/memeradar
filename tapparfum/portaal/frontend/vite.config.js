import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Statische build → dist/ (nul server). Deploy dist/ op Netlify/Vercel.
export default defineConfig({
  plugins: [vue()],
  server: { port: 5173 },
  build: { outDir: 'dist', sourcemap: true }
})
