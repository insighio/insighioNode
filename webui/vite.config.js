import { fileURLToPath, URL } from "node:url"

import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"

import { compression, defineAlgorithm } from "vite-plugin-compression2"
import { gzipAsync as zopfliGzip } from "@gfx/zopfli"

// The ESP32 serves plain HTTP, where browsers only accept gzip (not brotli).
// Zopfli produces standard gzip output that is ~3.5% smaller than zlib level 9.
const zopfli = defineAlgorithm((buf, options) => zopfliGzip(buf, options), { numiterations: 15 })

// A <link rel="stylesheet"> in <head> blocks the first paint, so the inline loading
// indicator would stay invisible until the CSS arrives from the ESP32. Loading it as
// "print" and switching to "all" on load keeps it non-blocking. The app is only
// revealed on window "load", which waits for this stylesheet, so nothing renders unstyled.
const nonBlockingCss = {
  name: "non-blocking-css",
  apply: "build",
  transformIndexHtml: {
    order: "post",
    handler: (html) =>
      html.replace(/<link rel="stylesheet"([^>]*?)>/g, (tag, attrs) =>
        attrs.includes("media=") ? tag : `<link rel="stylesheet"${attrs} media="print" onload="this.media='all'">`
      )
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), nonBlockingCss, compression({ algorithms: [zopfli], filename: "[path][base].gz" })],
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
        // Keep a single JS bundle: it gzips smaller and needs one less request to the ESP32.
        chunkFileNames: "assets/[name]-[hash].js",
        entryFileNames: "assets/[name]-[hash].js",
        assetFileNames: "assets/[name]-[hash].[ext]"
      }
    },
    chunkSizeWarningLimit: 600
  }
})
