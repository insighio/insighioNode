<template>
  <div class="panel-body">
    <br />
    <!--div id="loader" class="loading loading-lg"></div-->
    <div class="container grid-lg">
      <div class="columns flex-centered">
        <div class="column col-xl-7 col-md-10 col-sm-12">
          <div class="form-group">
            <div class="columns">
              <SDivider label="Available measurements" />
              <SSwitch label="LED notifications" v-model:value="ledEnabled" />
              <SSwitch label="Battery statistics" v-model:value="batteryStats" />
              <SSwitch label="Board humidity/temperature" v-model:value="boardSense" />
              <SSwitch label="Network statistics" v-model:value="networkStat" />
              <SSwitch label="OTA enabled" v-model:value="otaEnabled" />
              <SSwitch label="Store measurements if failed connection" v-model:value="storeMeasIfFailedConn" />
              <SSelect
                label="Temperature unit"
                v-model:value="temperatureUnitIsCelsius"
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
              <div class="accordion">
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
                          </tr>
                        </tbody>
                      </table>
                      <button class="btn btn-primary" @click="keyValuePairs.push({ key: '', value: '' })">
                        Add key-value pair
                      </button>
                    </div>
                  </div>
                  <br />
                </div>
              </div>
              <!--SDivider label="Explicit key-values" /-->

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
              <div class="col-12" v-for="(tab, index) in tabs" :key="index" v-show="activeTab === tab.id">
                <br />
                <br />
                <component :is="tab.component" @goNext="validateMyForm" @goBack="requestGoBack" />
              </div>
              <br />
              <br />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
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
//import ShieldAccelerometer from "./shields/ShieldAccelerometer.vue"

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
    ShieldAdvind
    // ShieldAccelerometer
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
        { id: "scale", label: "Shield Digital/Scale", component: "ShieldScale" },
        { id: "dig_analog", label: "Shield I2C/Analog", component: "ShieldDigitalAnalog" },
        { id: "advind", label: "Shield SDI-12", component: "ShieldAdvind" }
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
        dig_analog: "dig_analog"
      }
    }
  },
  mounted() {
    this.initializeValues()
  },
  methods: {
    initializeValues() {
      this.gpsEnabled = this.strToJSValue(this.$cookies.get("meas-gps-enabled"))

      this.ledEnabled = this.strToJSValue(this.$cookies.get("meas-led-enabled"), true)
      this.batteryStats = this.strToJSValue(this.$cookies.get("meas-battery-stat"), true)
      this.boardSense = this.strToJSValue(this.$cookies.get("meas-board-sense"), true)
      this.boardStat = this.strToJSValue(this.$cookies.get("meas-board-stat"), false)
      this.networkStat = this.strToJSValue(this.$cookies.get("meas-network-stat"), true)
      this.otaEnabled = this.strToJSValue(this.$cookies.get("system-enable-ota"), true)

      this.temperatureUnitIsCelsius = this.strToJSValue(this.$cookies.get("meas-temp-unit"), true)

      var selectedShield = this.$cookies.get("selected-shield")
        ? this.$cookies.get("selected-shield")
        : this.$cookies.get("selected-board")

      this.activeTab = this.backwardCompatibilitySelectedShield[selectedShield]
        ? this.backwardCompatibilitySelectedShield[selectedShield]
        : "scale"

      // boardChanged(undefined, tabNamePerShield[selectedShield])

      this.gpsTimeout = this.$cookies.get("meas-gps-timeout") ? this.$cookies.get("meas-gps-timeout") : 120
      this.gpsSatNum = this.$cookies.get("meas-gps-sat-num") ? this.$cookies.get("meas-gps-sat-num") : 4
      this.gpsNoFixNoUpload = this.strToJSValue(this.$cookies.get("meas-gps-no-fix-no-upload"), false)
      this.gpsOnlyOnBoot = this.strToJSValue(this.$cookies.get("meas-gps-only-on-boot"), false)

      this.storeMeasIfFailedConn = this.strToJSValue(this.$cookies.get("store-meas-if-failed-conn"), false)

      //fillKeyValuePairsFromDictionary(this.$cookies.get("meas-keyvalue"))
    },
    changeTab(tabId) {
      this.activeTab = tabId
    },
    validateMyForm() {
      // Add form validation and saving logic here
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
    },

    storeData() {
      this.clearCookies()

      this.$cookies.set("meas-led-enabled", this.boolElemToPyStr("input-led-enabled"))
      this.$cookies.set("meas-battery-stat", this.boolElemToPyStr("input-battery"))
      this.$cookies.set("meas-board-sense", this.boolElemToPyStr("input-board-sense"))
      this.$cookies.set("meas-board-stat", this.boolElemToPyStr("input-board-stat"))
      this.$cookies.set("meas-network-stat", this.boolElemToPyStr("input-network"))
      this.$cookies.set("system-enable-ota", this.boolElemToPyStr("input-ota"))
      this.$cookies.set("meas-gps-enabled", this.boolElemToPyStr("input-gps-enable"))

      console.log(
        "document.getElementById('input-gps-timeout').value: ",
        document.getElementById("input-temp-unit").value
      )
      this.$cookies.set(
        "meas-temp-unit",
        document.getElementById("input-temp-unit").value === "false" ? "False" : "True"
      )

      this.$cookies.set("meas-gps-timeout", document.getElementById("input-gps-timeout").value)
      this.$cookies.set("meas-gps-sat-num", document.getElementById("input-gps-sat-num").value)
      this.$cookies.set("meas-gps-no-fix-no-upload", this.boolElemToPyStr("input-gps-no-fix-no-upload"))
      this.$cookies.set("meas-gps-only-on-boot", this.boolElemToPyStr("input-gps-only-on-boot"))

      this.$cookies.set("store-meas-if-failed-conn", this.boolElemToPyStr("input-store-meas-if-failed-conn"))

      this.$cookies.set("meas-keyvalue", this.getKeyValuePairs())

      this.$cookies.set("selected-shield", this.activeTab)

      if (this.activeTab === "advind") {
        redirectoToMeasurementNaming()
      } else if (this.activeTab === "scale") {
        let scale = this.$cookies.get("meas-scale-scale")
        let offset = this.$cookies.get("meas-scale-offset")
        if (!isChecked("input-scale-enabled")) {
          this.$cookies.set("meas-scale-offset", 0)
          this.$cookies.set("meas-scale-scale", 1)
          redirectoToMeasurementNaming()
        } else {
          if (scale && offset) {
            this.$cookies.set("meas-scale-offset", offset)
            this.$cookies.set("meas-scale-scale", scale)
            redirectTo("step-5-3-scale-calibr-res.html")
          } else {
            redirectTo("step-5-1-scale-idle.html")
          }
        }
      } else if (this.activeTab === "dig_analog") {
        redirectoToMeasurementNaming()
      }
    },
    getKeyValuePairs() {
      let localObj = {}

      this.keyValuePairs.forEach((pair) => {
        if (pair.key && pair.value) {
          localObj[pair.key] = pair.value
        }
      })

      return localObj
    }
  }
}
</script>

<style scoped>
.measurements {
  /* Add your component styles here */
}
</style>
