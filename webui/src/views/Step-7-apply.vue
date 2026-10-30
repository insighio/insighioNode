<template>
  <div class="panel-body ui-pt-1">
    <div v-if="isLoading" class="loading loading-lg"></div>
    <div class="empty">
      <div v-show="!isLoading && !saveError" class="empty-icon">
        <i class="icon icon-2x icon-check"></i>
      </div>
      <p v-if="isLoading" class="empty-title h5">Applying Configuration...</p>
      <div v-else-if="saveError">
        <p class="empty-title h5">Configuration not saved</p>
        <p class="toast toast-error" role="alert">{{ saveError }}</p>
        <button class="btn btn-primary" @click="apply">Try again</button>
      </div>
      <div v-else>
        <p class="empty-title h5">Configuration Applied</p>
        <p class="empty-subtitle">The device will soon reboot to the desired configuration.</p>
      </div>

      <div class="empty-action" v-if="!isLoading">
        <button class="btn" @click="startOver">Start over</button>
      </div>
    </div>
  </div>
</template>

<script>
import { fetchInternal } from "@/js/utils.js"

export default {
  name: "Step7Apply",
  data() {
    return {
      isLoading: true,
      saveError: ""
    }
  },
  mounted() {
    this.apply()
  },
  methods: {
    apply() {
      this.isLoading = true
      this.saveError = ""
      const encodedParams = {}
      const config = {}
      let isConfigValid = false
      let requestFileSystemOptimization = this.$storage.get("request_fs_optimization")

      this.$storage.keys().forEach((key) => {
        let value = this.$storage.get(key)

        if (typeof value === "object") {
          value = JSON.stringify(value)
        }

        if (value === undefined || value === null || value === "null") return

        isConfigValid = true
        if (key === "wifi-ssid" || key === "wifi-pass") {
          encodedParams[key] = encodeURIComponent(value)
          config[key] = value.replaceAll("\\", "\\\\").replaceAll("'", "\\'")
        } else if (
          key === "meas-name-mapping" ||
          key === "meas-name-ext-mapping" ||
          key === "meas-keyvalue" ||
          key === "meas-sdi12" ||
          key === "meas-modbus" ||
          key === "meas-adc" ||
          key === "meas-pulseCounter" ||
          key === "system-settings" ||
          key === "secondary-measurement-transmission-info"
        ) {
          encodedParams[key] = encodeURIComponent(value)
          config[key] = value
        } else config[key] = value
      })

      if (!isConfigValid) {
        this.startOver()
        return
      }

      fetchInternal(
        "/save-config",
        30000,
        "POST",
        { queryParams: config, encodedParams, requestFileSystemOptimization },
        "json"
      )
        .then(() => {
          this.$storage.clear()
          this.requestReboot()
        })
        .catch((err) => {
          console.error("Error saving config:", err)
          this.isLoading = false
          this.saveError =
            "Could not save your configuration. Your settings are still available. Check your device connection and try again."
        })
    },
    requestReboot() {
      this.isLoading = false

      fetchInternal("/reboot", 30000, "POST", {}, "json")
        .then((res) => console.log(res))
        .catch((err) => {
          console.log("error rebooting: ", err)
        })
    },
    startOver() {
      this.$nextTick(() => {
        this.$storage.clear()
        this.tabActive = 0
        this.$storage.set("activeTab", this.tabActive)
        window.location.reload()
      })
    }
  }
}
</script>
