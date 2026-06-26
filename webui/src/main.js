import "@/assets/css/style.css"
import "@/assets/css/spectre.min.css"
import "@/assets/css/spectre-icons.min.css"
import "@/assets/css/special-tabs.css"
//import "@/assets/main.css"

import { createApp } from "vue"
import App from "./App.vue"
import StoragePlugin from "@/js/storage.js"

let app = createApp(App)
app.use(StoragePlugin, { expires: "35min" })
app.mount("#app")

// Add cache busting to all requests
const originalFetch = window.fetch
window.fetch = function (url, options = {}) {
  if (typeof url === "string" && url.startsWith("/")) {
    const separator = url.includes("?") ? "&" : "?"
    url = url + separator + "_cb=" + Date.now()
  }

  options.cache = "no-cache"
  options.headers = {
    ...options.headers,
    "Cache-Control": "no-cache, no-store, must-revalidate",
    Pragma: "no-cache"
  }

  return originalFetch(url, options)
}
