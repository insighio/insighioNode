<template>
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
</template>

<script>
export default {
  name: "Step7Apply",
  data() {
    return {
      isLoading: true,
      isFinished: false
    }
  },
  methods: {
    apply() {
      const encodedParams = {}
      const config = {}
      let isConfigValid = false

      this.$cookies.keys().forEach((key) => {
        const value = this.$cookies.get(key)
        isConfigValid = true
        config[key] =
          key === "wifi-ssid" || key === "wifi-pass" ? value.replaceAll("\\", "\\\\").replaceAll("'", "\\'") : value
        encodedParams[key] = encodeURIComponent(value)
      })

      if (!isConfigValid) {
        this.startOver()
        return
      }

      fetch("/save-config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ queryParams: config, encodedParams })
      })
        .then(() => {
          this.$cookies.keys().forEach((cookie) => this.$cookies.remove(cookie))
          this.requestReboot()
        })
        .catch((err) => console.error("Error saving config:", err))
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
