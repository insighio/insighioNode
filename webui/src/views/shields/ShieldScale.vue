<template>
  <div class="form-group columns">
    <SSelect
      label="I2C #1"
      v-model:value="i2c1"
      @update:value="i2c1 = $event"
      :valueOptions="i2cOptions"
      :colsLabel="4"
      :colsInput="8"
    />

    <SSelect
      label="I2C #2"
      v-model:value="i2c2"
      @update:value="i2c2 = $event"
      :valueOptions="i2cOptions"
      :colsLabel="4"
      :colsInput="8"
    />
    <SSelect
      label="Analog / Digital P1"
      v-model:value="adcP1"
      @update:value="adcP1 = $event"
      :valueOptions="adcOptions"
      :colsLabel="4"
      :colsInput="8"
    />
    <SSwitch
      label="Weight Scale"
      v-model:value="scaleEnabled"
      @update:value="scaleEnabled = $event"
      :colsLabel="4"
      :colsInput="8"
    />
    <SSwitch
      label="[Debug] Enable Scale Sensor Monitoring"
      v-model:value="scaleMonitoring"
      @update:value="scaleMonitoring = $event"
      :colsLabel="4"
      :colsInput="8"
    />
    <WebuiFooter @savePressed="validateMyForm" @backPressed="requestGoBack" />
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"
import ShieldCommonData from "@/components/mixins/ShieldCommonData.vue"
import WebuiFooter from "@/components/WebuiFooter.vue"

import SSwitch from "@/components/SSwitch.vue"
import SSelect from "@/components/SSelect.vue"

export default {
  name: "ShieldScale",
  mixins: [CommonTools, ShieldCommonData],
  components: { SSwitch, WebuiFooter, SSelect },
  data() {
    return {
      i2c1: "",
      i2c2: "",
      adcP1: "",
      scaleEnabled: false,
      scaleMonitoring: false
    }
  },
  mounted() {
    // Add your mounted logic here
    this.initializeValues()
  },
  methods: {
    initializeValues() {
      // Add initialization logic here
      this.i2c1 = this.$cookies.get("meas-i2c-1")
      this.i2c2 = this.$cookies.get("meas-i2c-2")
      this.adcP1 = this.$cookies.get("meas-sensor-a-d-p1")
      this.scaleEnabled = this.strToJSValue(this.$cookies.get("meas-scale-enabled"), false)
      this.scaleMonitoring = this.strToJSValue(this.$cookies.get("meas-scale-monitoring-enabled"), false)
    },
    // Add your component methods here
    validateMyForm() {
      this.requestGoNext()
    },
    clearCookies() {
      this.$cookies.remove("meas-i2c-1")
      this.$cookies.remove("meas-i2c-2")
      this.$cookies.remove("meas-sensor-a-d-p1")
      this.$cookies.remove("meas-sensor-a-d-p1-t")
      this.$cookies.remove("meas-sensor-scale-enabled")
      this.$cookies.remove("meas-scale-monitoring-enabled")
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

      this.$cookies.set("meas-keyvalue", getKeyValuePairs())

      if (elementIsVisible("shield-advind-options")) {
        this.$cookies.set("selected-shield", shieldNamePerTab["shield-advind-options"])

        for (let i = 1; i < 11; ++i) {
          setSDI12Cookie(i)
        }

        this.$cookies.set("meas-4-20-snsr-1-enable", this.boolElemToPyStr("ins-esp-gen-4-20-snsr-1-enable"))
        this.$cookies.set("meas-4-20-snsr-2-enable", this.boolElemToPyStr("ins-esp-gen-4-20-snsr-2-enable"))
        this.$cookies.set("meas-4-20-snsr-1-formula", document.getElementById("ins-esp-gen-4-20-snsr-1-formula").value)
        this.$cookies.set("meas-4-20-snsr-2-formula", document.getElementById("ins-esp-gen-4-20-snsr-2-formula").value)

        this.$cookies.set("meas-sdi-warmup-time", document.getElementById("input-gen-sdi12-warmup-time").value)

        this.$cookies.set("meas-pcnt-1-enable", this.boolElemToPyStr("ins-esp-gen-pcnt-1-enable"))
        ///this.$cookies.set('meas-pcnt-1-cnt-on-rising', document.getElementById('ins-esp-gen-pcnt-1-cnt-on').value === "rising")
        this.$cookies.set("meas-pcnt-1-formula", document.getElementById("ins-esp-gen-pcnt-1-formula").value)
        this.$cookies.set("meas-pcnt-1-high-freq", this.boolElemToPyStr("ins-esp-gen-pcnt-1-high-freq"))

        redirectoToMeasurementNaming()
      } else if (elementIsVisible("shield-scale-options")) {
        this.$cookies.set("selected-shield", shieldNamePerTab["shield-scale-options"])
        this.$cookies.set("meas-i2c-1", document.getElementById("input-i2c-1").value)
        this.$cookies.set("meas-i2c-2", document.getElementById("input-i2c-2").value)
        this.$cookies.set("meas-sensor-a-d-p1", document.getElementById("input-sensor-a-d-p1").value)
        this.$cookies.set("meas-scale-enabled", this.boolElemToPyStr("input-scale-enabled"))
        this.$cookies.set("meas-scale-monitoring-enabled", this.boolElemToPyStr("input-scale-monitoring"))

        if (!isChecked("input-scale-enabled")) {
          this.$cookies.set("meas-scale-offset", 0)
          this.$cookies.set("meas-scale-scale", 1)
          redirectoToMeasurementNaming()
        } else {
          var scale = this.$cookies.get("meas-scale-scale")
          var offset = this.$cookies.get("meas-scale-offset")

          console.log("offset: ", offset, ", scale:", scale)

          if (scale && offset) {
            this.$cookies.set("meas-scale-offset", offset)
            this.$cookies.set("meas-scale-scale", scale)
            redirectTo("step-5-3-scale-calibr-res.html")
          } else {
            redirectTo("step-5-1-scale-idle.html")
          }
        }
      } else if (elementIsVisible("shield-dig-analog-options")) {
        this.$cookies.set("selected-shield", shieldNamePerTab["shield-dig-analog-options"])
        this.$cookies.set("meas-i2c-1", document.getElementById("input-s1-i2c").value)
        this.$cookies.set("meas-sensor-a-d-p1", document.getElementById("input-s1-sensor-a-d-p1").value)
        this.$cookies.set("meas-sensor-a-d-p2", document.getElementById("input-s1-sensor-a-d-p2").value)
        this.$cookies.set("meas-sensor-a-d-p3", document.getElementById("input-s1-sensor-a-d-p3").value)

        if (elementIsVisible("input-s1-sensor-a-d-p1-trans-div"))
          this.$cookies.set("meas-sensor-a-d-p1-t", document.getElementById("input-s1-sensor-a-d-p1-t").value)

        if (elementIsVisible("input-s1-sensor-a-d-p2-trans-div"))
          this.$cookies.set("meas-sensor-a-d-p2-t", document.getElementById("input-s1-sensor-a-d-p2-t").value)

        if (elementIsVisible("input-s1-sensor-a-d-p3-trans-div"))
          this.$cookies.set("meas-sensor-a-d-p3-t", document.getElementById("input-s1-sensor-a-d-p3-t").value)

        redirectoToMeasurementNaming()
      }

      enableNavigationButtons()
    }
  },
  computed: {
    // Add your computed properties here
  }
}
</script>

<style scoped>
.network {
  /* Add your component styles here */
}
</style>
