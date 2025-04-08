import { fileURLToPath, URL } from "node:url"

import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"

import { compression } from "vite-plugin-compression2"

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), compression()],
  css: {
    postcss: "./postcss.config.js" // Specify the PostCSS configuration file
  },
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url))
    }
  }
})
