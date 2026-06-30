import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// base: './' usa rutas relativas para que funcione igual en GitHub Pages
// (subcarpeta /portfolio/), en Netlify (raiz) y en local.
export default defineConfig({
  base: './',
  plugins: [react()],
})
