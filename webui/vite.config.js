import { fileURLToPath, URL } from "node:url"

import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"

import { compression } from "vite-plugin-compression2"

// https://vite.dev/config/
export default defineConfig({
  // plugins: [
  //   vue(),
  //   compression({
  //     algorithm: "brotliCompress",
  //     threshold: 512,
  //     deleteOriginalAssets: true
  //   })
  // ],
  plugins: [vue(), compression()],
  css: {
    postcss: "./postcss.config.js" // Specify the PostCSS configuration file
  },
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url))
    }
  },
  build: {
    minify: "terser",
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ["console.log", "console.info", "console.debug"],
        passes: 2
      },
      mangle: {
        safari10: true
      },
      format: {
        comments: false
      }
    },
    cssMinify: "lightningcss",
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules")) {
            if (id.includes("vue")) {
              return "vue-core"
            }
          }
        },
        chunkFileNames: "assets/[name]-[hash].js",
        entryFileNames: "assets/[name]-[hash].js",
        assetFileNames: "assets/[name]-[hash].[ext]"
      }
    },
    chunkSizeWarningLimit: 600
  }
})
