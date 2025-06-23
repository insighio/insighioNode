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
      const config = {}
      //let isConfigValid = false
      let requestFileSystemOptimization = this.$cookies.get("request_fs_optimization")

      this.$cookies.keys().forEach((key) => {
        let value = this.$cookies.get(key)

        if (typeof value === "string") {
          try {
            value = JSON.parse(value)
            config[key] = value
          } catch (e) {
            // If parsing fails, keep the original string value
          }
        }

        config[key] = value
      })

      fetch("http://192.168.4.1" + "/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ config, requestFileSystemOptimization })
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
