<template>
  <div>
    <div class="header-container">
      <img src="@/assets/img/logo.png" class="img-responsive px-2 py-2 img-center" />

      <!-- Settings Button and Menu -->
      <div class="settings-container" v-if="tabActive > 0">
        <button class="btn btn-primary settings-btn" @click="toggleSettingsMenu" ref="settingsButton">
          <i class="icon icon-more-vert"></i>
        </button>

        <div v-if="showSettingsMenu" class="settings-menu" @click.stop>
          <button class="btn btn-link menu-item" @click="downloadMeasurements">
            <i class="icon icon-download" style="margin-right: 5px"></i>Download Measurements
          </button>
          <button class="btn btn-link menu-item" @click="showRebootConfirm = true">
            <i class="icon icon-refresh" style="margin-right: 5px"></i>Reboot
          </button>
          <div class="menu-separator"></div>
          <button class="btn btn-link menu-item" @click="showFactoryResetConfirm = true">
            <i class="icon icon-delete" style="margin-right: 5px"></i>Factory Reset
          </button>
          <div class="menu-separator"></div>
        </div>
      </div>
    </div>

    <div class="panel panel-custom">
      <div class="panel-header" v-if="tabActive === 1">
        <div class="panel-title text-center">Welcome to insigh.io device configuration.</div>
      </div>

      <div class="columns">
        <div class="panel-nav col-12 hide-sm">
          <br />

          <ul class="step">
            <li v-for="tab in tabs" class="step-item" :key="tab" :class="{ active: tabActive === tabs.indexOf(tab) }">
              <a>{{ tab }}</a>
            </li>
          </ul>
        </div>
      </div>

      <div>
        <Step1Login v-if="tabActive === 0" @goNext="goToNextStep" />
        <Step2Network v-else-if="tabActive === 1" @goNext="goToNextStep" @goBack="goToPreviousStep" />
        <Step3APIKeys
          v-else-if="tabActive === 2 && networkTech !== 'lora'"
          @goNext="goToNextStep"
          @goBack="goToPreviousStep"
        />
        <Step3LoRaKeys
          v-else-if="tabActive === 2 && networkTech === 'lora'"
          @goNext="goToNextStep"
          @goBack="goToPreviousStep"
        />

        <Step4Measurements v-else-if="tabActive === 3" @goNext="goToNextStep" @goBack="goToPreviousStep" />
        <Step5Timing v-else-if="tabActive === 4" @goNext="goToNextStep" @goBack="goToPreviousStep" />
        <Step6Verify v-else-if="tabActive === 5" @goNext="goToNextStep" @goBack="goToPreviousStep" />
        <Step7Apply v-else-if="tabActive === 6" @start-over="goToStart" />
      </div>
    </div>

    <div v-if="showRebootConfirm" class="modal active">
      <div class="modal-overlay" @click="showRebootConfirm = false"></div>
      <div class="modal-container">
        <div class="modal-header">
          <div class="modal-title h5">Confirm Device Reboot</div>
        </div>
        <div class="modal-body">
          <p>
            Are you sure you want to perform a device reboot? The device will restart and continue with the execution of
            defined configuration.
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-primary" @click="requestReboot" :disabled="isRebooting">
            {{ isRebooting ? "Rebooting..." : "Confirm Reboot" }}
          </button>
          <button class="btn btn-link" @click="showRebootConfirm = false" :disabled="isRebooting">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Factory Reset Confirmation Modal -->
    <div v-if="showFactoryResetConfirm" class="modal active">
      <div class="modal-overlay" @click="showFactoryResetConfirm = false"></div>
      <div class="modal-container">
        <div class="modal-header">
          <div class="modal-title h5">Confirm Factory Reset</div>
        </div>
        <div class="modal-body">
          <p>
            Are you sure you want to perform a factory reset? This action cannot be undone and will erase all device
            configuration.
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-primary" @click="factoryReset" :disabled="isResetting">
            {{ isResetting ? "Resetting..." : "Confirm Reset" }}
          </button>
          <button class="btn btn-link" @click="showFactoryResetConfirm = false" :disabled="isResetting">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import "@/assets/css/spectre.min.css"
import Step1Login from "@/views/Step-1-Login.vue"
import Step2Network from "@/views/Step-2-Network.vue"
import Step3APIKeys from "@/views/Step-3-APIKeys.vue"
import Step3LoRaKeys from "@/views/Step-3-LoRa-Keys.vue"
import Step4Measurements from "@/views/Step-4-Measurements.vue"
import Step5Timing from "@/views/Step-5-Timing.vue"
import Step6Verify from "@/views/Step-6-Verify.vue"
import Step7Apply from "@/views/Step-7-apply.vue"

export default {
  name: "MainPage",
  components: {
    Step1Login,
    Step2Network,
    Step3APIKeys,
    Step3LoRaKeys,
    Step4Measurements,
    Step5Timing,
    Step6Verify,
    Step7Apply
  },
  data() {
    return {
      tabs: ["Login", "Network", "API Keys", "Measurements", "Timing", "Verify", "Apply"],
      tabActive: -1,
      networkTech: "",
      showSettingsMenu: false,
      showFactoryResetConfirm: false,
      showRebootConfirm: false,
      isResetting: false,
      isRebooting: false
    }
  },
  mounted() {
    let storedActiveTab = this.$cookies.get("activeTab")

    console.log("storedActiveTab: ", storedActiveTab)
    if (storedActiveTab !== undefined && storedActiveTab !== null) this.tabActive = parseInt(storedActiveTab)
    else {
      this.tabActive = 0
      this.$cookies.set("activeTab", this.tabActive)
    }

    this.networkTech = this.$cookies.get("network")

    // Close settings menu when clicking outside
    document.addEventListener("click", this.handleOutsideClick)
  },
  beforeUnmount() {
    document.removeEventListener("click", this.handleOutsideClick)
  },
  methods: {
    goToNextStep() {
      this.networkTech = this.$cookies.get("network")

      this.tabActive += 1

      this.$cookies.set("activeTab", this.tabActive)

      console.log("goToNextStep: ", this.tabActive)
      //networkTech
    },
    goToPreviousStep() {
      this.tabActive -= 1

      this.$cookies.set("activeTab", this.tabActive)

      console.log("goToPrevStep: ", this.tabActive)
    },
    goToStart() {
      this.tabActive = 1
      this.$cookies.set("activeTab", this.tabActive)
      const savedSession = this.$cookies.get("session")
      this.$cookies.keys().forEach((cookie) => this.$cookies.remove(cookie))
      this.$cookies.set("session", savedSession)
    },
    toggleSettingsMenu() {
      this.showSettingsMenu = !this.showSettingsMenu
    },
    handleOutsideClick(event) {
      if (!this.$refs.settingsButton || !this.$refs.settingsButton.contains(event.target)) {
        this.showSettingsMenu = false
      }
    },
    async downloadMeasurements() {
      try {
        this.showSettingsMenu = false
        const response = await fetch("http://192.168.4.1" + "/saved_meas", {
          method: "GET",
          headers: {
            Accept: "application/json"
          }
        })

        if (response.ok) {
          const data = await response.json()

          // Create a downloadable file
          const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" })
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement("a")
          a.href = url
          a.download = `measurements_${new Date().toISOString().split(".")[0].replaceAll(":", "")}.json`
          document.body.appendChild(a)
          a.click()
          window.URL.revokeObjectURL(url)
          document.body.removeChild(a)

          console.log("Measurements downloaded successfully")
        } else {
          console.error("Failed to download measurements:", response.statusText)
          alert("Failed to download measurements. Please try again.")
        }
      } catch (error) {
        console.error("Error downloading measurements:", error)
        alert("Error downloading measurements. Please check your connection and try again.")
      }
    },
    async factoryReset() {
      this.isResetting = true

      try {
        const response = await fetch("http://192.168.4.1" + "/api/factory_reset", {
          method: "POST",
          headers: {
            Accept: "application/json, text/plain, */*",
            "Content-Type": "application/json"
          }
        })

        if (response.ok) {
          alert("Factory reset completed successfully. The device will restart.")
          // Clear all cookies and redirect to start
          this.$cookies.keys().forEach((cookie) => this.$cookies.remove(cookie))
          this.showFactoryResetConfirm = false
          this.$cookies.keys().forEach((cookie) => this.$cookies.remove(cookie))
          this.tabActive = 0
          this.$cookies.set("activeTab", this.tabActive)
        } else {
          console.error("Factory reset failed:", response.statusText)
          alert("Factory reset failed. Please try again.")
        }
      } catch (error) {
        console.error("Error during factory reset:", error)
        alert("Error during factory reset. Please check your connection and try again.")
      } finally {
        this.isResetting = false
      }
    },
    requestReboot() {
      this.isRebooting = true

      fetch("http://192.168.4.1" + "/reboot", {
        method: "POST",
        headers: {
          Accept: "application/json, text/plain, */*",
          "Content-Type": "application/json"
        },
        body: "{}"
      })
        .then((res) => {
          console.log(res)
          this.isRebooting = false
          this.$cookies.keys().forEach((cookie) => this.$cookies.remove(cookie))
          this.tabActive = 0
          this.$cookies.set("activeTab", this.tabActive)
        })
        .catch((err) => {
          console.log("error rebooting: ", err)
          this.isRebooting = false
        })
    }
  },
  setup() {
    console.log("accessing setup")
  }
}
</script>

<style scoped>
.header-container {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.settings-container {
  position: relative;
  margin-top: 1rem;
  margin-right: 1rem;
}

.settings-btn {
  font-size: 0.9rem;
  padding: 0.4rem 0.8rem;
  border-radius: 0.25rem;
}

.settings-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 0.25rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  min-width: 200px;
  margin-top: 0.25rem;
}

.menu-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: 0.75rem 1rem;
  border: none;
  background: none;
  color: #333;
  text-decoration: none;
  transition: background-color 0.2s;
}

.menu-item:hover {
  background-color: #f5f5f5;
  color: #333;
  text-decoration: none;
}

.menu-item:first-child {
  border-top-left-radius: 0.25rem;
  border-top-right-radius: 0.25rem;
}

.menu-item:last-child {
  border-bottom-left-radius: 0.25rem;
  border-bottom-right-radius: 0.25rem;
}

.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.vue:hover {
  filter: drop-shadow(0 0 2em #42b883aa);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .header-container {
    flex-direction: column;
    align-items: center;
  }

  .settings-container {
    margin: 0.5rem 0;
  }

  .settings-menu {
    right: auto;
    left: 50%;
    transform: translateX(-50%);
  }
}

.menu-separator {
  height: 1px;
  background-color: #e0e0e0;
  margin: 0.25rem 0;
}
</style>
