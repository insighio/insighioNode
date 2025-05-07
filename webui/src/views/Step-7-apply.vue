<template>
  <div class="panel-body">
    <br />
    <div v-if="isLoading" class="loading loading-lg"></div>
    <div class="empty">
      <div v-show="!isLoading" class="empty-icon">
        <i class="icon icon-2x icon-check"></i>
      </div>
      <p v-if="isLoading" class="empty-title h5">Applying Configuration...</p>
      <div v-else>
        <p class="empty-title h5">Configuration Applied</p>
        <p class="empty-subtitle">The device will soon reboot to the desired configuration.</p>
      </div>

      <div class="empty-action">
        <button class="btn btn-primary" @click="startOver">Start over?</button>
      </div>
      <br />
      <br />
    </div>
  </div>
</template>

<script>
export default {
  name: "Step7Apply",
  data() {
    return {
      isLoading: true
    }
  },
  mounted() {
    this.apply()
  },
  methods: {
    apply() {
      const encodedParams = {}
      const config = {}
      let isConfigValid = false
      let requestFileSystemOptimization = this.$cookies.get("request_fs_optimization")

      this.$cookies.keys().forEach((key) => {
        let value = this.$cookies.get(key)

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
          key === "system-settings"
        ) {
          encodedParams[key] = encodeURIComponent(value)
          config[key] = value
        } else config[key] = value
      })

      if (!isConfigValid) {
        this.startOver()
        return
      }

      fetch("http://192.168.4.1" + "/save-config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ queryParams: config, encodedParams, requestFileSystemOptimization })
      })
        .then(() => {
          this.$cookies.keys().forEach((cookie) => this.$cookies.remove(cookie))
          this.requestReboot()
        })
        .catch((err) => console.error("Error saving config:", err))
    },
    requestReboot() {
      this.isLoading = false

      fetch("http://192.168.4.1" + "/reboot", {
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
    },
    startOver() {
      this.$emit("startOver")
    }
  }
}
</script>
