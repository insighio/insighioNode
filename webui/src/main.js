//import './assets/main.css'
import "@/assets/css/style.css"

import { createApp } from "vue"
import App from "./App.vue"
import VueCookies from "vue-cookies"

let app = createApp(App)
app.use(VueCookies, { expires: "35min" })
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
