//import './assets/main.css'
import "@/assets/css/style.css"

import { createApp } from "vue"
import App from "./App.vue"
import VueCookies from "vue-cookies"

let app = createApp(App)
app.use(VueCookies, { expires: "35min" })
app.mount("#app")
