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

      this.$cookies.set("meas-i2c-1", this.i2c1)
      this.$cookies.set("meas-i2c-2", this.i2c2)
      this.$cookies.set("meas-sensor-a-d-p1", this.adcP1)
      this.$cookies.set("meas-scale-enabled", this.boolToPyStr(this.scaleEnabled))
      this.$cookies.set("meas-scale-monitoring-enabled", this.boolToPyStr(this.scaleMonitoring))

      if (!this.scaleEnabled) {
        this.$cookies.set("meas-scale-offset", 0)
        this.$cookies.set("meas-scale-scale", 1)
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

      this.requestGoNext()
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
