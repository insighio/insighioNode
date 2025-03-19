<template>
  <div class="body-custom">
    <img src="@/assets/logo.png" class="img-responsive px-2 py-2 img-center" alt="Logo" />

    <div class="panel panel-custom">
      <div class="columns">
        <div class="panel-nav col-12 hide-sm">
          <br />
          <ul class="step">
            <li class="step-item"><a>Login</a></li>
            <li class="step-item"><a>Select Network</a></li>
            <li class="step-item"><a>Network Params</a></li>
            <li class="step-item"><a>API Keys</a></li>
            <li class="step-item"><a>Measurements</a></li>
            <li class="step-item"><a>Timing</a></li>
            <li class="step-item"><a>Verify</a></li>
          </ul>
          <br />
          <hr />
        </div>
      </div>

      <div class="panel-body">
        <br />
        <div v-if="isLoading" id="loader" class="loading loading-lg"></div>
        <div class="empty">
          <div v-show="isFinished" id="finished_icon_1" class="empty-icon">
            <i class="icon icon-2x icon-check"></i>
          </div>
          <p v-if="isLoading" id="loading_label_1" class="empty-title h5">Applying Configuration...</p>
          <p v-show="isFinished" id="finished_label_1" class="empty-title h5">Configuration Applied</p>
          <p v-show="isFinished" id="finished_label_2" class="empty-subtitle">
            The device will soon reboot to the desired configuration.
          </p>
          <div class="empty-action">
            <button class="btn btn-primary" id="save-button" @click="startOver">Start over?</button>
          </div>
          <br />
          <br />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Cookies from "js-cookie"
import { redirectTo, showElement } from "@/utils"

export default {
  name: "Step7Apply",
  data() {
    return {
      isLoading: true,
      isFinished: false
    }
  },
  methods: {
    startOver() {
      redirectTo("step-2-select.html")
    },
    apply() {
      const config = Cookies.get()
      const encodedParams = {}
      let isConfigValid = false

      for (let key in config) {
        if (config.hasOwnProperty(key)) {
          isConfigValid = true
          if (key === "wifi-ssid" || key === "wifi-pass") {
            encodedParams[key] = encodeURIComponent(config[key])
            config[key] = config[key].replaceAll("\\", "\\\\").replaceAll("'", "\\'")
          } else if (key === "meas-name-mapping" || key === "meas-name-ext-mapping" || key === "meas-keyvalue") {
            encodedParams[key] = encodeURIComponent(config[key])
          }
        }
      }

      console.log("queryParams: ", config)
      const objToSend = { queryParams: config, encodedParams }

      if (!isConfigValid) {
        this.startOver()
        return
      }

      fetch("/save-config", {
        method: "POST",
        headers: {
          Accept: "application/json, text/plain, */*",
          "Content-Type": "application/json"
        },
        body: JSON.stringify(objToSend)
      })
        .then(() => {
          for (let key in config) {
            Cookies.remove(key)
          }
          this.requestReboot()
        })
        .catch((err) => {
          console.log("error saving config: ", err)
        })
    },
    requestReboot() {
      this.isLoading = false
      this.isFinished = true

      fetch("/reboot", {
        method: "POST",
        headers: {
          Accept: "application/json, text/plain, */*",
          "Content-Type": "application/json"
        },
        body: "{}"
      })
        .then((res) => console.log(res))
        .catch((err) => {
          console.log("error rebooting: ", err)
        })
    }
  },
  mounted() {
    this.apply()
  }
}
</script>

<style scoped>
/* Add any custom styles here if needed */
</style>
