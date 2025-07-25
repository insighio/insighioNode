<template>
  <div class="panel-body">
    <br />
    <!--div class="loading loading-lg"></div-->
    <div class="container grid-lg">
      <div class="columns flex-centered">
        <div class="column col-xl-7 col-md-10 col-sm-12">
          <div class="container">
            <div class="columns">
              <SDivider label="Available measurements" />
              <SSwitch label="Battery statistics" v-model:value="batteryStats" />
              <SSwitch label="Board humidity/temperature" v-model:value="boardSense" />
              <SSwitch label="Network statistics" v-model:value="networkStat" />
              <SSwitch label="Store measurements if failed connection" v-model:value="storeMeasIfFailedConn" />
              <SSelect
                label="Temperature unit"
                v-model:value="temperatureUnitIsCelsius"
                @update:value="temperatureUnitIsCelsius = $event"
                :valueOptions="temperatureUnitOptions"
              />
              <SSwitch label="GPS enabled" v-model:value="gpsEnabled" />

              <div v-if="gpsEnabled" style="margin: 20px" class="columns flex-centered col-12">
                <SInput label="GPS Timeout (seconds)" v-model:value="gpsTimeout" type="number" />
                <SInput label="Min number of satellites" v-model:value="gpsSatNum" type="number" />

                <SSwitch label="Discard measurements if no GPS fix" v-model:value="gpsNoFixNoUpload" />
                <SSwitch label="GPS only on boot" v-model:value="gpsOnlyOnBoot" />
              </div>
              <br />

              <SDivider label="Explicit key-values" />
              <div class="accordion col-12">
                <input type="checkbox" id="accordion-1" name="accordion-checkbox" hidden />
                <label class="accordion-header" for="accordion-1">
                  <i class="icon icon-arrow-right mr-1"></i>
                  Explicit key-values
                </label>
                <div class="accordion-body">
                  <div class="columns">
                    <div class="col-12">
                      <table class="table">
                        <thead>
                          <tr>
                            <th>Key</th>
                            <th>Value</th>
                            <th>
                              <button class="btn btn-primary" @click="keyValuePairs.push({ key: '', value: '' })">
                                <i class="icon icon-plus"></i>
                              </button>
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="(pair, index) in keyValuePairs" :key="index">
                            <td>
                              <input type="text" v-model="pair.key" placeholder="key name" style="width: 100%" />
                            </td>
                            <td>
                              <input type="text" v-model="pair.value" placeholder="key value" style="width: 100%" />
                            </td>
                            <td>
                              <button class="btn btn-primary" @click="keyValuePairs.splice(index, 1)">
                                <i class="icon icon-delete"></i>
                              </button>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                  <br />
                </div>
              </div>

              <SDivider label="Advanced System Settings" />
              <div class="accordion col-12">
                <input type="checkbox" id="accordion-2" name="accordion-checkbox" hidden />
                <label class="accordion-header" for="accordion-2">
                  <i class="icon icon-arrow-right mr-1"></i>
                  System
                </label>
                <div class="accordion-body">
                  <div class="columns col-12" style="margin: 10px">
                    <SSwitch label="LED notifications" v-model:value="ledEnabled" />
                    <SSwitch label="OTA enabled" v-model:value="otaEnabled" />
                    <SSelect
                      label="Logging Level"
                      v-model:value="systemSettings.loggingLevel"
                      @update:value="systemSettings.loggingLevel = $event"
                      :valueOptions="loggingLevels"
                    />
                    <SSwitch
                      label="File System Optimization"
                      v-model:value="systemSettings.enableFileSystemOptimization"
                    />
                  </div>
                  <br />
                </div>
              </div>

              <SDivider label="Shield Selection" />

              <div class="col-12">
                <ul class="tab tab-block">
                  <li
                    v-for="(tab, index) in tabs"
                    :key="index"
                    :class="['tab-item', { active: activeTab === tab.id }]"
                    @click="changeTab(tab.id)"
                  >
                    <a class="pointer">{{ tab.label }}</a>
                  </li>
                </ul>
              </div>
              <br />
              <div class="col-12" v-for="(tab, index) in tabs" :key="index">
                <transition :name="transitionDirection" mode="out-in">
                  <div v-if="activeTab === tab.id" :key="tab.id">
                    <br />
                    <br />
                    <component :is="tab.component" @goNext="validateMyForm" @goBack="requestGoBack" />
                  </div>
                </transition>
              </div>
              <br />
              <br />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <CustomNamingDialog v-model:isOpen="isMeasurementNamingDialogOpen" @save="closeAndProceed" @close="closeAndStay" />
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"
import SSwitch from "@/components/SSwitch.vue"
import SInput from "@/components/SInput.vue"
import SDivider from "@/components/SDivider.vue"
import SSelect from "@/components/SSelect.vue"
import ShieldScale from "./shields/ShieldScale.vue"
import ShieldDigitalAnalog from "./shields/ShieldDigitalAnalog.vue"
import ShieldAdvind from "./shields/ShieldAdvind.vue"
import ShieldEnviro from "./shields/ShieldEnviro.vue"
import CustomNamingDialog from "@/views/aux/CustomNamingDialog.vue"

export default {
  name: "Step4Measurements",
  mixins: [CommonTools],
  components: {
    SSwitch,
    SInput,
    SDivider,
    SSelect,
    ShieldScale,
    ShieldDigitalAnalog,
    ShieldAdvind,
    ShieldEnviro,
    CustomNamingDialog
  },
  data() {
    return {
      ledEnabled: true,
      batteryStats: true,
      boardSense: true,
      boardStat: false,
      networkStat: true,
      otaEnabled: true,
      storeMeasIfFailedConn: true,
      temperatureUnitIsCelsius: true,
      gpsEnabled: true,
      gpsTimeout: 120,
      gpsSatNum: 4,
      gpsNoFixNoUpload: false,
      gpsOnlyOnBoot: false,
      i2c1: "",
      i2c2: "",
      scaleEnabled: false,
      analogDigitalP1: "",
      keyValuePairs: [{ key: "", value: "" }],
      temperatureUnitOptions: [
        { value: true, label: "Celsius (C)" },
        { value: false, label: "Fahrenheit (F)" }
      ],
      tabs: [
        { id: "scale", label: "Digital/Scale", component: "ShieldScale" },
        { id: "dig_analog", label: "I2C/Analog", component: "ShieldDigitalAnalog" },
        { id: "advind", label: "SDI-12", component: "ShieldAdvind" },
        { id: "enviro", label: "SDI-12/Modbus/ADC", component: "ShieldEnviro" }
        //{ id: "accel", label: "Shield Accelerometer", component: "ShieldAccelerometer" }
      ],
      activeTab: "scale",
      backwardCompatibilitySelectedShield: {
        accel: "accel",
        ins_esp_gen_sdi12: "advind",
        ins_esp_gen_1: "scale",
        ins_gen_s3: "dig_analog",
        advind: "advind",
        scale: "scale",
        dig_analog: "dig_analog",
        enviro: "enviro"
      },
      loggingLevels: [
        { value: "DEBUG", label: "Debug" },
        { value: "INFO", label: "Info" },
        { value: "WARNING", label: "Warning" },
        { value: "ERROR", label: "Error" }
      ],
      systemDefaultSettings: {
        loggingLevel: "DEBUG",
        enableFileSystemOptimization: true
      },
      systemSettings: {
        loggingLevel: "DEBUG",
        enableFileSystemOptimization: true
      },
      transitionDirection: "slide-left", // Default transition direction
      isMeasurementNamingDialogOpen: false,
      measurements: [],
      unitOptions: ["Celsius", "Fahrenheit", "Kelvin"] // Example units
    }
  },
  mounted() {
    this.initializeValues()
  },
  methods: {
    initializeValues() {
      const getCookieValue = (key, defaultValue) => this.$cookies.get(key) ?? defaultValue

      this.gpsEnabled = this.getValueWithDefaults(getCookieValue("meas-gps-enabled", true))
      this.ledEnabled = this.getValueWithDefaults(getCookieValue("meas-led-enabled", true))
      this.batteryStats = this.getValueWithDefaults(getCookieValue("meas-battery-stat", true))
      this.boardSense = this.getValueWithDefaults(getCookieValue("meas-board-sense", true))
      this.boardStat = this.getValueWithDefaults(getCookieValue("meas-board-stat", false))
      this.networkStat = this.getValueWithDefaults(getCookieValue("meas-network-stat", true))
      this.otaEnabled = this.getValueWithDefaults(getCookieValue("system-enable-ota", true))
      this.temperatureUnitIsCelsius = this.getValueWithDefaults(getCookieValue("meas-temp-unit", true))

      var selectedShield = this.$cookies.get("selected-shield")
        ? this.$cookies.get("selected-shield")
        : this.$cookies.get("selected-board")

      this.activeTab = this.backwardCompatibilitySelectedShield[selectedShield]
        ? this.backwardCompatibilitySelectedShield[selectedShield]
        : "scale"

      // boardChanged(undefined, tabNamePerShield[selectedShield])

      this.gpsTimeout = this.$cookies.get("meas-gps-timeout") ? this.$cookies.get("meas-gps-timeout") : 120
      this.gpsSatNum = this.$cookies.get("meas-gps-sat-num") ? this.$cookies.get("meas-gps-sat-num") : 4
      this.gpsNoFixNoUpload = this.getValueWithDefaults(this.$cookies.get("meas-gps-no-fix-no-upload"), false)
      this.gpsOnlyOnBoot = this.getValueWithDefaults(this.$cookies.get("meas-gps-only-on-boot"), false)

      this.storeMeasIfFailedConn = this.getValueWithDefaults(this.$cookies.get("store-meas-if-failed-conn"), false)

      this.systemSettings = this.getJsonObjectFromCookies("system-settings")
        ? this.getJsonObjectFromCookies("system-settings")
        : this.systemDefaultSettings

      //fillKeyValuePairsFromDictionary(this.$cookies.get("meas-keyvalue"))
    },
    changeTab(tabId) {
      // Add form validation and saving logic here
      const currentIndex = this.tabs.findIndex((tab) => tab.id === this.activeTab)
      const newIndex = this.tabs.findIndex((tab) => tab.id === tabId)

      console.log("Current index:", currentIndex, ", New index:", newIndex)

      // Determine transition direction
      this.transitionDirection = newIndex > currentIndex ? "slide-left" : "slide-right"

      console.log("Transition direction:", this.transitionDirection)

      // Update the active tab
      this.activeTab = tabId
    },
    validateMyForm() {
      this.storeData()
    },
    clearCookies() {
      this.$cookies.remove("meas-led-enabled")
      this.$cookies.remove("meas-battery-stat")
      this.$cookies.remove("meas-board-sense")
      this.$cookies.remove("meas-board-stat")
      this.$cookies.remove("meas-gps-enabled")
      this.$cookies.remove("meas-gps-no-fix-no-upload")
      this.$cookies.remove("meas-gps-only-on-boot")
      this.$cookies.remove("meas-gps-sat-num")
      this.$cookies.remove("meas-gps-timeout")
      this.$cookies.remove("meas-network-stat")
      this.$cookies.remove("meas-temp-unit")
      this.$cookies.remove("selected-shield")
      this.$cookies.remove("system-enable-ota")
      this.$cookies.remove("meas-keyvalue")
      this.$cookies.remove("store-meas-if-failed-conn")
      this.$cookies.remove("system-settings")
      this.$cookies.remove("request_fs_optimization")
    },

    storeData() {
      this.clearCookies()

      this.$cookies.set("meas-led-enabled", this.ledEnabled)
      this.$cookies.set("meas-battery-stat", this.batteryStats)
      this.$cookies.set("meas-board-sense", this.boardSense)
      this.$cookies.set("meas-board-stat", this.boardStat)
      this.$cookies.set("meas-network-stat", this.networkStat)
      this.$cookies.set("system-enable-ota", this.otaEnabled)
      this.$cookies.set("meas-gps-enabled", this.gpsEnabled)
      this.$cookies.set("meas-temp-unit", this.temperatureUnitIsCelsius)

      this.$cookies.set("meas-gps-timeout", this.gpsTimeout)
      this.$cookies.set("meas-gps-sat-num", this.gpsSatNum)
      this.$cookies.set("meas-gps-no-fix-no-upload", this.gpsNoFixNoUpload)
      this.$cookies.set("meas-gps-only-on-boot", this.gpsOnlyOnBoot)

      this.$cookies.set("store-meas-if-failed-conn", this.storeMeasIfFailedConn)

      this.$cookies.set("meas-keyvalue", this.getKeyValuePairs())

      this.$cookies.set("selected-shield", this.activeTab)

      this.$cookies.set("system-settings", this.systemSettings)
      this.$cookies.set("request_fs_optimization", this.systemSettings.enableFileSystemOptimization)

      //this.requestGoNext()
      this.openMeasurementNamingDialog()
    },
    getKeyValuePairs() {
      let localObj = {}

      this.keyValuePairs.forEach((pair) => {
        if (pair.key && pair.value) {
          localObj[pair.key] = pair.value
        }
      })

      return localObj
    },
    openMeasurementNamingDialog() {
      this.isMeasurementNamingDialogOpen = true
    },
    closeAndStay() {
      this.isMeasurementNamingDialogOpen = false
    },
    closeAndProceed() {
      this.isMeasurementNamingDialogOpen = false
      this.requestGoNext()
    }
  }
}
</script>

<style scoped>
.slide-left-enter-active,
.slide-left-leave-active {
  transition:
    transform 0.3s ease,
    opacity 0.3s ease;
}
.slide-left-enter {
  transform: translateX(100%);
  opacity: 0;
}
.slide-left-leave-to {
  transform: translateX(-100%);
  opacity: 0;
}

.slide-right-enter-active,
.slide-right-leave-active {
  transition:
    transform 0.3s ease,
    opacity 0.3s ease;
}
.slide-right-enter {
  transform: translateX(-100%);
  opacity: 0;
}
.slide-right-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-container {
  background: white;
  border-radius: 5px;
  width: 90%;
  max-width: 1000px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.modal-header {
  padding: 1rem;
  border-bottom: 1px solid #e5e5e5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-body {
  padding: 1rem;
}

.modal-footer {
  padding: 1rem;
  border-top: 1px solid #e5e5e5;
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}
</style>
