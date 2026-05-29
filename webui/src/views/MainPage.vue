<template>
  <div>
    <div class="header-container">
      <div class="container">
        <div class="columns">
          <div class="column col-10">
            <img src="@/assets/img/logo.png" class="img-responsive px-2" />
          </div>
          <div class="column col-2" style="display: flex; justify-content: flex-end; align-items: center">
            <!-- Settings Button and Menu -->
            <div class="settings-container" :style="{ height: '100%', margin: '0' }" v-if="tabActive > 0">
              <button
                class="btn settings-btn"
                :style="{ height: '100%', margin: '0' }"
                @click="toggleSettingsMenu"
                ref="settingsButton"
              >
                <!--i class="icon icon-more-vert"></i-->
                <i class="icon icon-menu"></i>
              </button>
            </div>
          </div>
          <div v-if="showSettingsMenu" class="settings-menu" @click.stop>
            <button class="btn btn-link menu-item" @click="downloadMeasurements">
              <i class="icon icon-download" style="margin-right: 5px"></i>Download Measurements
            </button>
            <button class="btn btn-link menu-item" @click="clearMeasurements">
              <i class="icon icon-delete" style="margin-right: 5px"></i>Clear Measurements
            </button>
            <div class="menu-separator"></div>
            <button class="btn btn-link menu-item" @click="resetSession">
              <i class="icon icon-refresh" style="margin-right: 5px"></i>Reset Session
            </button>
            <div class="menu-separator"></div>
            <button class="btn btn-link menu-item" @click="downloadConfiguration">
              <i class="icon icon-download" style="margin-right: 5px"></i>Download Configuration
            </button>
            <button class="btn btn-link menu-item" @click="importConfiguration">
              <i class="icon icon-upload" style="margin-right: 5px"></i>Import Configuration
            </button>
            <div class="menu-separator"></div>
            <button class="btn btn-link menu-item" @click="doUploadOTA">
              <i class="icon icon-upload" style="margin-right: 5px"></i>Upload OTA
            </button>
            <div class="menu-separator"></div>
            <button class="btn btn-link menu-item" @click="doShowRebootConfirm">
              <i class="icon icon-shutdown" style="margin-right: 5px"></i>Reboot
            </button>
            <div class="menu-separator"></div>
            <button class="btn btn-link menu-item" @click="showFactoryResetConfirm = true">
              <i class="icon icon-cross" style="margin-right: 5px"></i>Factory Reset
            </button>
            <div class="menu-separator"></div>
          </div>
        </div>
      </div>
    </div>

    <div class="panel panel-custom">
      <div class="columns">
        <div class="panel-nav col-12 hide-sm">
          <br />

          <div class="toast" v-if="showToast">{{ toastMessage }}</div>

          <ul class="step">
            <li v-for="tab in tabs" class="step-item" :key="tab" :class="{ active: tabActive === tabs.indexOf(tab) }">
              <a>{{ tab }}</a>
            </li>
          </ul>
        </div>
      </div>

      <div>
        <Step1Login v-if="tabActive === 0" :key="'step1-' + configVersion" @goNext="goToNextStep" />
        <Step2Network
          v-else-if="tabActive === 1"
          :key="'step2-' + configVersion"
          @goNext="goToNextStep"
          @goBack="goToPreviousStep"
        />
        <Step3APIKeys
          v-else-if="tabActive === 2 && networkTech !== 'lora'"
          :key="'step3api-' + configVersion"
          @goNext="goToNextStep"
          @goBack="goToPreviousStep"
        />
        <Step3LoRaKeys
          v-else-if="tabActive === 2 && networkTech === 'lora'"
          :key="'step3lora-' + configVersion"
          @goNext="goToNextStep"
          @goBack="goToPreviousStep"
        />

        <Step4Measurements
          v-else-if="tabActive === 3"
          :key="'step4-' + configVersion"
          @goNext="goToNextStep"
          @goBack="goToPreviousStep"
        />
        <Step5Timing
          v-else-if="tabActive === 4"
          :key="'step5-' + configVersion"
          @goNext="goToNextStep"
          @goBack="goToPreviousStep"
        />
        <Step6Verify
          v-else-if="tabActive === 5"
          :key="'step6-' + configVersion"
          @goNext="goToNextStep"
          @goBack="goToPreviousStep"
        />
        <Step7Apply v-else-if="tabActive === 6" :key="'step7-' + configVersion" @start-over="goToStart" />
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

    <!-- OTA Upload Modal -->
    <div v-if="showOTAUploadModal" class="modal active">
      <div class="modal-overlay" @click="closeOTAModal"></div>
      <div class="modal-container">
        <div class="modal-header">
          <div class="modal-title h5">Upload OTA Package</div>
        </div>
        <div class="modal-body">
          <p>Select a .tar OTA package file to upload (max 500KB).</p>
          <div class="form-group">
            <input
              type="file"
              ref="otaFileInput"
              @change="handleFileSelect"
              accept=".tar"
              class="form-input"
              :disabled="isUploading"
            />
          </div>
          <div v-if="selectedFile" class="file-info">
            <p><strong>File:</strong> {{ selectedFile.name }}</p>
            <p><strong>Size:</strong> {{ formatFileSize(selectedFile.size) }}</p>
          </div>
          <div v-if="uploadError" class="toast toast-error">
            {{ uploadError }}
          </div>
          <div v-if="uploadProgress > 0 && uploadProgress < 100" class="upload-progress">
            <div class="bar">
              <div class="bar-item" :style="{ width: uploadProgress + '%' }" role="progressbar"></div>
            </div>
            <p>Uploading: {{ uploadProgress }}%</p>
          </div>
        </div>
        <div class="modal-footer">
          <button
            class="btn btn-primary"
            @click="uploadOTAFile"
            :disabled="!selectedFile || isUploading || fileSizeError"
          >
            {{ isUploading ? "Uploading..." : "Upload" }}
          </button>
          <button class="btn btn-link" @click="closeOTAModal" :disabled="isUploading">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Import Configuration Modal -->
    <div v-if="showImportConfigModal" class="modal active">
      <div class="modal-overlay" @click="closeImportConfigModal"></div>
      <div class="modal-container">
        <div class="modal-header">
          <div class="modal-title h5">Import Configuration</div>
        </div>
        <div class="modal-body">
          <p>Select a configuration file (.py) to import settings.</p>
          <div class="form-group">
            <input
              type="file"
              ref="configFileInput"
              @change="handleConfigFileSelect"
              accept=".py"
              class="form-input"
              :disabled="isImporting"
            />
          </div>
          <SSwitch v-model:value="importAPIKeys" label="Import API Keys" :disabled="isImporting" />
          <div v-if="selectedConfigFile" class="file-info">
            <p><strong>File:</strong> {{ selectedConfigFile.name }}</p>
            <p><strong>Size:</strong> {{ formatFileSize(selectedConfigFile.size) }}</p>
          </div>
          <div v-if="importError" class="toast toast-error">
            {{ importError }}
          </div>
          <div v-if="importProgress > 0 && importProgress < 100" class="upload-progress">
            <div class="bar">
              <div class="bar-item" :style="{ width: importProgress + '%' }" role="progressbar"></div>
            </div>
            <p>Importing: {{ importProgress }}%</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-primary" @click="uploadConfigFile" :disabled="!selectedConfigFile || isImporting">
            {{ isImporting ? "Importing..." : "Import" }}
          </button>
          <button class="btn btn-link" @click="closeImportConfigModal" :disabled="isImporting">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Settings Synchronization Loading Overlay -->
    <div v-if="isSynchingSettings" class="modal active">
      <div class="modal-overlay"></div>
      <div class="modal-container" style="background: transparent; box-shadow: none">
        <div class="modal-body" style="text-align: center; background: white; border-radius: 0.5rem; padding: 2rem">
          <div class="loading loading-lg"></div>
          <p style="margin-top: 1rem; font-size: 1rem; color: #333">Loading device settings...</p>
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
import { fetchInternal } from "@/js/utils.js"
import SSwitch from "@/components/SSwitch.vue"

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
    Step7Apply,
    SSwitch
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
      isRebooting: false,
      showToast: false,
      toastMessage: "",
      showOTAUploadModal: false,
      selectedFile: null,
      isUploading: false,
      uploadError: null,
      uploadProgress: 0,
      fileSizeError: false,
      maxFileSize: 500 * 1024, // 500KB in bytes
      showImportConfigModal: false,
      selectedConfigFile: null,
      importAPIKeys: false,
      isImporting: false,
      importError: null,
      importProgress: 0,
      configVersion: 0, // Incremented to force component remount when config is imported
      isSynchingSettings: false // Loading state for settings synchronization
    }
  },
  mounted() {
    let storedActiveTab = this.$storage.get("activeTab")

    console.log("storedActiveTab: ", storedActiveTab)
    if (storedActiveTab !== undefined && storedActiveTab !== null) this.tabActive = parseInt(storedActiveTab)
    else {
      this.tabActive = 0
      this.$storage.set("activeTab", this.tabActive)
    }

    this.networkTech = this.$storage.get("network")

    // Close settings menu when clicking outside
    document.addEventListener("click", this.handleOutsideClick)
  },
  beforeUnmount() {
    document.removeEventListener("click", this.handleOutsideClick)
  },
  methods: {
    async goToNextStep() {
      // if tabActive is 0 (login page) and goToNextStep is called,
      // get the settings of the device.
      if (this.tabActive === 0) {
        await this.synchSettings()
      }

      this.$nextTick(() => {
        this.tabActive += 1

        this.$storage.set("activeTab", this.tabActive)

        console.log("goToNextStep: ", this.tabActive)
        if (this.tabActive === 1) {
          this.updateDeviceSystemTime()
        }
      })
    },
    async synchSettings() {
      this.isSynchingSettings = true
      this.$storage.clear()

      try {
        let data = await fetchInternal("/settings")
        Object.keys(data).forEach((key) => {
          this.$storage.set(key.replaceAll("_", "-"), data[key])
        })
      } catch (err) {
        console.log("error completing request", err)
      } finally {
        this.isSynchingSettings = false
      }
    },
    goToPreviousStep() {
      this.tabActive -= 1

      this.$storage.set("activeTab", this.tabActive)

      console.log("goToPrevStep: ", this.tabActive)
      if (this.tabActive === 1) {
        this.updateDeviceSystemTime()
      }
    },
    goToStart() {
      this.tabActive = 1
      this.$storage.set("activeTab", this.tabActive)
      const savedSession = this.$storage.get("session")
      this.$storage.clear()
      this.$storage.set("session", savedSession)
    },
    showToastMessage(message, timeout = 2000) {
      this.toastMessage = message
      this.showToast = true
      setTimeout(() => {
        this.showToast = false
        this.toastMessage = ""
      }, timeout)
    },
    toggleSettingsMenu() {
      this.showSettingsMenu = !this.showSettingsMenu
    },
    handleOutsideClick(event) {
      if (!this.$refs.settingsButton || !this.$refs.settingsButton.contains(event.target)) {
        this.showSettingsMenu = false
      }
    },
    convertJSONObjectToSenmlObject(deviceId, jsonObj) {
      const senmlObj = []
      let baseTime = undefined

      for (const key in jsonObj) {
        const measObj = {}

        if (key === "dt") {
          baseTime = jsonObj[key]["value"]
          continue
        }

        measObj["n"] = key

        if (jsonObj[key]["unit"]) {
          measObj["u"] = jsonObj[key]["unit"]
        }

        let v = jsonObj[key]["value"]
        if (v !== undefined) {
          if (typeof v === "number") {
            measObj["v"] = parseFloat(jsonObj[key]["value"])
          } else if (typeof v === "boolean") {
            measObj["vb"] = jsonObj[key]["value"] === true || jsonObj[key]["value"] === "true"
          } else if (typeof v === "string") {
            measObj["vs"] = jsonObj[key]["value"]
          }
        }

        senmlObj.push(measObj)
      }

      if (senmlObj.length > 0) {
        senmlObj[0]["bn"] = deviceId
        if (baseTime !== undefined) {
          senmlObj[0]["bt"] = baseTime
        }
      }

      return senmlObj
    },
    async downloadMeasurements() {
      try {
        this.showSettingsMenu = false

        // Fetch the streamed measurements file
        const response = await fetchInternal("/api/saved_meas", 30000, "GET", null, "response")

        if (response.ok) {
          // Get the raw text content
          const textContent = await response.text()

          // Parse metadata and data
          const metadataMatch = textContent.match(/### METADATA ###\n(.+?)\n### DATA ###\n/s)
          let metadata = { device_id: "unknown" }
          let dataContent = textContent

          if (metadataMatch) {
            try {
              metadata = JSON.parse(metadataMatch[1])
              dataContent = textContent.substring(metadataMatch[0].length)
            } catch (e) {
              console.warn("Could not parse metadata:", e)
            }
          }

          // Get API keys from cookies
          const insighio_id = this.$storage.get("insighio-id")
          const insighio_key = this.$storage.get("insighio-key")
          const insighio_channel = this.$storage.get("insighio-channel")

          // Create final file content with metadata
          const fileContent = {
            device_id: metadata.device_id,
            //format: metadata.format || "newline-delimited-json",
            keys: {
              insighio_id: insighio_id,
              insighio_key: insighio_key,
              insighio_channel: insighio_channel
            },
            measurements: dataContent
              .split("\n")
              .filter((line) => line.trim())
              .map((line) => {
                try {
                  return this.convertJSONObjectToSenmlObject(metadata.device_id, JSON.parse(line))
                } catch (e) {
                  return null
                }
              })
              .filter((item) => item !== null)
          }

          // Create downloadable file
          //const blob = new Blob([JSON.stringify(fileContent, null, 2)], { type: "application/json" })
          const blob = new Blob([JSON.stringify(fileContent)], { type: "application/json" })
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
    async clearMeasurements() {
      this.showSettingsMenu = false
      try {
        await fetchInternal("/clear_measurements", 30000, "POST", {})

        alert("Measurements cleared successfully.")
        console.log("Measurements cleared successfully")
      } catch (error) {
        console.error("Error clearing measurements:", error)
        alert("Error clearing measurements. Please check your connection and try again.")
      }
    },
    async factoryReset() {
      this.isResetting = true

      try {
        await fetchInternal("/factory_reset", 30000, "POST", {})

        alert("Factory reset completed successfully. The device will restart.")

        this.showFactoryResetConfirm = false
        this.$storage.clear()
        this.tabActive = 0
        this.$storage.set("activeTab", this.tabActive)
      } catch (error) {
        console.error("Error during factory reset:", error)
        alert("Error during factory reset. Please check your connection and try again.")
      } finally {
        this.isResetting = false
      }
    },
    requestReboot() {
      this.isRebooting = true
      this.showSettingsMenu = false

      fetchInternal("/reboot", 30000, "POST", {})
        .then((res) => {
          console.log(res)
          this.isRebooting = false
          this.showRebootConfirm = false
          this.$storage.clear()
          this.tabActive = 0
          this.$storage.set("activeTab", this.tabActive)
        })
        .catch((err) => {
          console.log("error rebooting: ", err)
          this.isRebooting = false
          this.showRebootConfirm = false
        })
    },
    updateDeviceSystemTime() {
      // get browser time and send it to /api/time as HTTP post
      this.showSettingsMenu = false
      const now = new Date()
      const timestamp = Math.floor(now.getTime() / 1000)
      const body = { epoch: timestamp }
      fetchInternal("/api/time", 30000, "POST", body)
        .then((res) => {
          this.showToastMessage("Device system time updated successfully.")
        })
        .catch((err) => {
          console.log("error setting device time: ", err)
          alert("Error updating device system time. Please check your connection and try again.")
        })
    },
    doShowRebootConfirm() {
      this.showRebootConfirm = true
      this.showSettingsMenu = false
    },
    doUploadOTA() {
      this.showSettingsMenu = false
      this.showOTAUploadModal = true
      this.selectedFile = null
      this.uploadError = null
      this.uploadProgress = 0
      this.fileSizeError = false
    },
    closeOTAModal() {
      if (!this.isUploading) {
        this.showOTAUploadModal = false
        this.selectedFile = null
        this.uploadError = null
        this.uploadProgress = 0
        this.fileSizeError = false
        if (this.$refs.otaFileInput) {
          this.$refs.otaFileInput.value = ""
        }
      }
    },
    handleFileSelect(event) {
      const file = event.target.files[0]
      if (!file) {
        this.selectedFile = null
        this.fileSizeError = false
        return
      }

      // Check file extension
      if (!file.name.endsWith(".tar")) {
        this.uploadError = "Only .tar files are accepted."
        this.selectedFile = null
        this.fileSizeError = true
        return
      }

      // Check file size
      if (file.size > this.maxFileSize) {
        this.uploadError = `File size exceeds maximum allowed size of 500KB. Selected file is ${this.formatFileSize(
          file.size
        )}.`
        this.selectedFile = null
        this.fileSizeError = true
        return
      }

      this.selectedFile = file
      this.uploadError = null
      this.fileSizeError = false
    },
    formatFileSize(bytes) {
      if (bytes < 1024) return bytes + " B"
      else if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + " KB"
      else return (bytes / (1024 * 1024)).toFixed(2) + " MB"
    },
    async uploadOTAFile() {
      if (!this.selectedFile) return

      this.isUploading = true
      this.uploadError = null
      this.uploadProgress = 0

      try {
        const xhr = new XMLHttpRequest()

        // Track upload progress
        xhr.upload.addEventListener("progress", (e) => {
          if (e.lengthComputable) {
            this.uploadProgress = Math.round((e.loaded / e.total) * 100)
          }
        })

        // Handle completion
        const uploadPromise = new Promise((resolve, reject) => {
          xhr.addEventListener("load", () => {
            if (xhr.status === 200) {
              resolve()
            } else {
              reject(new Error(`Upload failed with status: ${xhr.status}`))
            }
          })
          xhr.addEventListener("error", () => reject(new Error("Network error during upload")))
          xhr.addEventListener("abort", () => reject(new Error("Upload cancelled")))
        })

        // Open request
        xhr.open("POST", "http://192.168.4.1/api/upload_ota", true)

        // Send raw file data directly (server will use a fixed filename)
        xhr.send(this.selectedFile)

        await uploadPromise

        // Success
        this.uploadProgress = 100

        this.showToastMessage(
          "OTA package uploaded successfully! The device will now apply the update and restart. You may need to reconnect."
        )
        this.isUploading = false
        this.closeOTAModal()

        // Clear storage and reset to login screen
        this.$storage.clear()
        this.tabActive = 0
        this.$storage.set("activeTab", this.tabActive)
      } catch (error) {
        console.error("Error uploading OTA file:", error)
        this.uploadError = error.message || "Failed to upload OTA package. Please try again."
        this.uploadProgress = 0
      } finally {
        this.isUploading = false
      }
    },
    async downloadConfiguration() {
      try {
        this.showSettingsMenu = false

        // Fetch the configuration file
        const response = await fetchInternal("/api/download_config", 30000, "GET", null, "response")

        if (response.ok) {
          // Get the configuration content
          const configContent = await response.text()

          // Extract filename from Content-Disposition header or use default
          let filename = "config.py"
          const contentDisposition = response.headers.get("Content-Disposition")
          if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="(.+)"/)
            if (filenameMatch) {
              filename = filenameMatch[1]
            }
          }

          // Create downloadable file
          const blob = new Blob([configContent], { type: "text/x-python" })
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement("a")
          a.href = url
          a.download = filename
          document.body.appendChild(a)
          a.click()
          window.URL.revokeObjectURL(url)
          document.body.removeChild(a)

          console.log("Configuration downloaded successfully")
        } else {
          console.error("Failed to download configuration:", response.statusText)
          alert("Failed to download configuration. Please try again.")
        }
      } catch (error) {
        console.error("Error downloading configuration:", error)
        alert("Error downloading configuration. Please check your connection and try again.")
      }
    },
    importConfiguration() {
      this.showSettingsMenu = false
      this.showImportConfigModal = true
      this.selectedConfigFile = null
      this.importError = null
      this.importProgress = 0
    },
    closeImportConfigModal() {
      if (!this.isImporting) {
        this.showImportConfigModal = false
        this.selectedConfigFile = null
        this.importError = null
        this.importProgress = 0
        if (this.$refs.configFileInput) {
          this.$refs.configFileInput.value = ""
        }
      }
    },
    handleConfigFileSelect(event) {
      const file = event.target.files[0]
      if (!file) {
        this.selectedConfigFile = null
        return
      }

      // Check file extension
      if (!file.name.endsWith(".py")) {
        this.importError = "Only .py configuration files are accepted."
        this.selectedConfigFile = null
        return
      }

      this.selectedConfigFile = file
      this.importError = null
    },
    async uploadConfigFile() {
      if (!this.selectedConfigFile) return

      this.isImporting = true
      this.importError = null
      this.importProgress = 0

      try {
        const xhr = new XMLHttpRequest()

        // Track upload progress
        xhr.upload.addEventListener("progress", (e) => {
          if (e.lengthComputable) {
            this.importProgress = Math.round((e.loaded / e.total) * 50) // First 50% for upload
          }
        })

        // Handle completion
        const uploadPromise = new Promise((resolve, reject) => {
          xhr.addEventListener("load", () => {
            if (xhr.status === 200) {
              try {
                const settings = JSON.parse(xhr.responseText)
                resolve(settings)
              } catch (e) {
                reject(new Error("Failed to parse response"))
              }
            } else {
              reject(new Error(`Upload failed with status: ${xhr.status}`))
            }
          })
          xhr.addEventListener("error", () => reject(new Error("Network error during upload")))
          xhr.addEventListener("abort", () => reject(new Error("Upload cancelled")))
        })

        // Open request
        xhr.open("POST", "http://192.168.4.1/api/upload_config", true)

        // Send raw file data
        xhr.send(this.selectedConfigFile)

        const settings = await uploadPromise

        // Update progress to 75% after upload completes
        this.$nextTick(() => {
          this.importProgress = 75
        })
        //this.importProgress = 75

        let backedUpKeys = {}

        console.log("importAPIKeys: ", this.importAPIKeys)
        if (!this.importAPIKeys) {
          //backup API keys from current settings before clearing storage
          backedUpKeys["insighio-id"] = this.$storage.get("insighio-id")
          backedUpKeys["insighio-key"] = this.$storage.get("insighio-key")
          backedUpKeys["insighio-channel"] = this.$storage.get("insighio-channel")
          backedUpKeys["insighio-control-channel"] = this.$storage.get("insighio-control-channel")
        }
        this.$storage.clear()
        Object.keys(settings).forEach((key) => {
          this.$storage.set(key.replaceAll("_", "-"), settings[key])
        })

        if (!this.importAPIKeys) {
          //restore backedUpKeys
          Object.keys(backedUpKeys).forEach((key) => {
            if (backedUpKeys[key]) {
              this.$storage.set(key, backedUpKeys[key])
            }
          })
        }

        // Update progress to 100%

        this.importProgress = 100

        // Increment configVersion to force component remount
        this.configVersion++

        this.$nextTick(() => {
          this.showToastMessage(
            "Configuration imported successfully! The settings have been loaded. Please review and save them."
          )
          this.isImporting = false
          this.closeImportConfigModal()

          // Navigate to Network step to review the imported settings
          this.tabActive = 1
          this.$storage.set("activeTab", this.tabActive)

          // Update network tech from imported settings
          this.networkTech = this.$storage.get("network")
        })
      } catch (error) {
        console.error("Error importing configuration:", error)
        this.importError = error.message || "Failed to import configuration. Please try again."
        this.importProgress = 0
      } finally {
        this.isImporting = false
      }
    },
    resetSession() {
      this.showSettingsMenu = false
      this.$nextTick(() => {
        if (confirm("Are you sure you want to reset the session? All unsaved configuration will be lost.")) {
          this.$storage.clear()
          this.tabActive = 0
          this.$storage.set("activeTab", this.tabActive)
        }
      })
      console.log("to delete")
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

/* .settings-container {
  position: relative;
  margin-top: 1rem;
  margin-right: 1rem;
} */

/* .settings-btn {
  font-size: 0.8rem;
  padding: 0.4rem 0.6rem;
  border-radius: 0.25rem;
}  */

.settings-btn {
  font-size: 0.8rem;
  padding: 0.4rem 0.8rem;
  border: none;
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

  /* .settings-container {
    margin: 0.5rem 0;
  } */

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

/* OTA Upload Modal Styles */
.file-info {
  margin-top: 1rem;
  padding: 0.75rem;
  background-color: #f8f9fa;
  border-radius: 0.25rem;
  border: 1px solid #e0e0e0;
}

.file-info p {
  margin: 0.25rem 0;
  font-size: 0.9rem;
}

.upload-progress {
  margin-top: 1rem;
}

.upload-progress .bar {
  height: 0.5rem;
  background-color: #f0f0f0;
  border-radius: 0.25rem;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.upload-progress .bar-item {
  height: 100%;
  background-color: #5755d9;
  transition: width 0.3s ease;
}

.upload-progress p {
  margin: 0;
  font-size: 0.9rem;
  text-align: center;
  color: #666;
}

.toast-error {
  margin-top: 1rem;
  padding: 0.75rem;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 0.25rem;
  color: #721c24;
}
</style>
