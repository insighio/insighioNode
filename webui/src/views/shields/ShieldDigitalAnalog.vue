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
      label="Analog / Digital P1"
      v-model:value="analogDigitalP1"
      @update:value="analogDigitalP1 = $event"
      :valueOptions="adcOptions"
      :colsLabel="4"
      :colsInput="8"
    />

    <div v-if="analogDigitalP1 === 'analog'" class="col-12">
      <div class="form-group columns">
        <div class="column col-1 col-mr-auto"></div>
        <div class="column col-9 col-mr-auto">
          <SInput
            label="P1 transformation"
            v-model:value="analogDigitalP1Transformation"
            @update:value="analogDigitalP1Transformation = $event"
            :colsLabel="4"
            :colsInput="8"
            :tooltip="tooltip"
          />
        </div>
        <div class="column col-2 col-mr-auto"></div>
      </div>
      <br />
    </div>
    <br />
    <br />
    <SSelect
      label="Analog / Digital P2"
      v-model:value="analogDigitalP2"
      @update:value="analogDigitalP2 = $event"
      :valueOptions="adcOptions"
      :colsLabel="4"
      :colsInput="8"
    />
    <div v-if="analogDigitalP2 === 'analog'" class="col-12">
      <div class="form-group columns">
        <div class="column col-1 col-mr-auto"></div>
        <div class="column col-9 col-mr-auto">
          <SInput
            label="P2 transformation"
            v-model:value="analogDigitalP2Transformation"
            @update:value="analogDigitalP2Transformation = $event"
            :colsLabel="4"
            :colsInput="8"
            :tooltip="tooltip"
          />
        </div>
        <div class="column col-2 col-mr-auto"></div>
      </div>
      <br />
    </div>
    <br />
    <br />
    <SSelect
      label="Analog / Digital P3"
      v-model:value="analogDigitalP3"
      @update:value="analogDigitalP3 = $event"
      :valueOptions="adcOptions"
      :colsLabel="4"
      :colsInput="8"
    />
    <div v-if="analogDigitalP3 === 'analog'" class="col-12">
      <div class="form-group columns">
        <div class="column col-1 col-mr-auto"></div>
        <div class="column col-9 col-mr-auto">
          <SInput
            label="P3 transformation"
            v-model:value="analogDigitalP3Transformation"
            @update:value="analogDigitalP3Transformation = $event"
            :colsLabel="4"
            :colsInput="8"
            :tooltip="tooltip"
          />
        </div>
        <div class="column col-2 col-mr-auto"></div>
        <br />
      </div>
    </div>
    <br />
    <br />
    <WebuiFooter @savePressed="validateMyForm" @backPressed="requestGoBack" />
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"
import ShieldCommonData from "@/components/mixins/ShieldCommonData.vue"
import WebuiFooter from "@/components/WebuiFooter.vue"
import SInput from "@/components/SInput.vue"
import SSelect from "@/components/SSelect.vue"

export default {
  name: "ShieldDigitalAnalog",
  mixins: [CommonTools, ShieldCommonData],
  components: { SSelect, WebuiFooter, SInput },
  data() {
    return {
      // Add your component data here
      i2c1: "disabled",
      analogDigitalP1: "disabled",
      analogDigitalP1Transformation: "v",
      analogDigitalP2: "disabled",
      analogDigitalP2Transformation: "v",
      analogDigitalP3: "disabled",
      analogDigitalP3Transformation: "v",
      tooltip: "python script to\ntransform raw value (v)\nfrom millivolt\nto meaningful value\nex: 2*v + v**2"
    }
  },
  methods: {
    initializeValues() {
      this.i2c1 = this.$cookies.get("meas-i2c-1")
      this.analogDigitalP1 = this.$cookies.get("meas-sensor-a-d-p1")
      this.analogDigitalP2 = this.$cookies.get("meas-sensor-a-d-p2")
      this.analogDigitalP3 = this.$cookies.get("meas-sensor-a-d-p3")
      this.analogDigitalP1Transformation = this.$cookies.get("meas-sensor-a-d-p1-t")
        ? this.$cookies.get("meas-sensor-a-d-p1-t")
        : "v"
      this.analogDigitalP2Transformation = this.$cookies.get("meas-sensor-a-d-p2-t")
        ? this.$cookies.get("meas-sensor-a-d-p2-t")
        : "v"
      this.analogDigitalP3Transformation = this.$cookies.get("meas-sensor-a-d-p3-t")
        ? this.$cookies.get("meas-sensor-a-d-p3-t")
        : "v"
    },
    // Add your component methods here
    validateMyForm() {
      this.requestGoNext()
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
      this.$cookies.remove("meas-i2c-1")
      this.$cookies.remove("meas-i2c-2")
      this.$cookies.remove("meas-network-stat")
      this.$cookies.remove("meas-scale-enabled")
      this.$cookies.remove("meas-sensor-a-d-p1")
      this.$cookies.remove("meas-sensor-a-d-p1-t")
      this.$cookies.remove("meas-sensor-a-d-p2")
      this.$cookies.remove("meas-sensor-a-d-p2-t")
      this.$cookies.remove("meas-sensor-a-d-p3")
      this.$cookies.remove("meas-sensor-a-d-p3-t")
      this.$cookies.remove("meas-sensor-scale-enabled")
      this.$cookies.remove("meas-temp-unit")
      this.$cookies.remove("selected-shield")
      this.$cookies.remove("system-enable-ota")
      this.$cookies.remove("meas-keyvalue")
      this.$cookies.remove("store-meas-if-failed-conn")
      this.$cookies.remove("meas-4-20-snsr-1-enable")
      this.$cookies.remove("meas-4-20-snsr-2-enable")
      this.$cookies.remove("meas-4-20-snsr-1-formula")
      this.$cookies.remove("meas-4-20-snsr-2-formula")
      this.$cookies.remove("meas-scale-monitoring-enabled")
      this.$cookies.remove("meas-pcnt-1-enable")
      this.$cookies.remove("meas-pcnt-1-cnt-on-rising")
      this.$cookies.remove("meas-pcnt-1-formula")
      this.$cookies.remove("meas-pcnt-1-high-freq")

      for (let i = 1; i < 11; ++i) {
        this.$cookies.remove("meas-sdi-" + i + "-enabled")
        this.$cookies.remove("meas-sdi-" + i + "-address")
        this.$cookies.remove("meas-sdi-" + i + "-loc")
      }
    },

    storeData() {
      disableNavigationButtons()
      clearthis.$cookies()

      this.$cookies.set("meas-led-enabled", boolElemToPyStr("input-led-enabled"))
      this.$cookies.set("meas-battery-stat", boolElemToPyStr("input-battery"))
      this.$cookies.set("meas-board-sense", boolElemToPyStr("input-board-sense"))
      this.$cookies.set("meas-board-stat", boolElemToPyStr("input-board-stat"))
      this.$cookies.set("meas-network-stat", boolElemToPyStr("input-network"))
      this.$cookies.set("system-enable-ota", boolElemToPyStr("input-ota"))
      this.$cookies.set("meas-gps-enabled", boolElemToPyStr("input-gps-enable"))

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
      this.$cookies.set("meas-gps-no-fix-no-upload", boolElemToPyStr("input-gps-no-fix-no-upload"))
      this.$cookies.set("meas-gps-only-on-boot", boolElemToPyStr("input-gps-only-on-boot"))

      this.$cookies.set("store-meas-if-failed-conn", boolElemToPyStr("input-store-meas-if-failed-conn"))

      this.$cookies.set("meas-keyvalue", getKeyValuePairs())

      if (elementIsVisible("shield-advind-options")) {
        this.$cookies.set("selected-shield", shieldNamePerTab["shield-advind-options"])

        for (let i = 1; i < 11; ++i) {
          setSDI12Cookie(i)
        }

        this.$cookies.set("meas-4-20-snsr-1-enable", boolElemToPyStr("ins-esp-gen-4-20-snsr-1-enable"))
        this.$cookies.set("meas-4-20-snsr-2-enable", boolElemToPyStr("ins-esp-gen-4-20-snsr-2-enable"))
        this.$cookies.set("meas-4-20-snsr-1-formula", document.getElementById("ins-esp-gen-4-20-snsr-1-formula").value)
        this.$cookies.set("meas-4-20-snsr-2-formula", document.getElementById("ins-esp-gen-4-20-snsr-2-formula").value)

        this.$cookies.set("meas-sdi-warmup-time", document.getElementById("input-gen-sdi12-warmup-time").value)

        this.$cookies.set("meas-pcnt-1-enable", boolElemToPyStr("ins-esp-gen-pcnt-1-enable"))
        ///this.$cookies.set('meas-pcnt-1-cnt-on-rising', document.getElementById('ins-esp-gen-pcnt-1-cnt-on').value === "rising")
        this.$cookies.set("meas-pcnt-1-formula", document.getElementById("ins-esp-gen-pcnt-1-formula").value)
        this.$cookies.set("meas-pcnt-1-high-freq", boolElemToPyStr("ins-esp-gen-pcnt-1-high-freq"))

        redirectoToMeasurementNaming()
      } else if (elementIsVisible("shield-scale-options")) {
        this.$cookies.set("selected-shield", shieldNamePerTab["shield-scale-options"])
        this.$cookies.set("meas-i2c-1", document.getElementById("input-i2c-1").value)
        this.$cookies.set("meas-i2c-2", document.getElementById("input-i2c-2").value)
        this.$cookies.set("meas-sensor-a-d-p1", document.getElementById("input-sensor-a-d-p1").value)
        this.$cookies.set("meas-scale-enabled", boolElemToPyStr("input-scale-enabled"))
        this.$cookies.set("meas-scale-monitoring-enabled", boolElemToPyStr("input-scale-monitoring"))

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
  },
  mounted() {
    // Add your mounted logic here
    this.initializeValues()
  }
}
</script>

<style scoped>
.network {
  /* Add your component styles here */
}
</style>
