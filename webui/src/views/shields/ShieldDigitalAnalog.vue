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

    <div v-if="adc1TransformationIsVisible" class="column col-12">
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
    <div v-if="adc2TransformationIsVisible" class="column col-12">
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
    <div v-if="adc3TransformationIsVisible" class="column col-12">
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
  computed: {
    adc1TransformationIsVisible() {
      return this.analogDigitalP1 === "analog"
    },
    adc2TransformationIsVisible() {
      return this.analogDigitalP2 === "analog"
    },
    adc3TransformationIsVisible() {
      return this.analogDigitalP3 === "analog"
    }
  },
  mounted() {
    // Add your mounted logic here
    this.initializeValues()
  },
  methods: {
    initializeValues() {
      this.i2c1 = this.strToJSValue(this.$cookies.get("meas-i2c-1"), "disabled")
      this.analogDigitalP1 = this.strToJSValue(this.$cookies.get("meas-sensor-a-d-p1"), "disabled")
      this.analogDigitalP2 = this.strToJSValue(this.$cookies.get("meas-sensor-a-d-p2"), "disabled")
      this.analogDigitalP3 = this.strToJSValue(this.$cookies.get("meas-sensor-a-d-p3"), "disabled")
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
      this.storeData()
    },
    clearCookies() {
      this.$cookies.remove("meas-i2c-1")
      this.$cookies.remove("meas-sensor-a-d-p1")
      this.$cookies.remove("meas-sensor-a-d-p1-t")
      this.$cookies.remove("meas-sensor-a-d-p2")
      this.$cookies.remove("meas-sensor-a-d-p2-t")
      this.$cookies.remove("meas-sensor-a-d-p3")
      this.$cookies.remove("meas-sensor-a-d-p3-t")
    },

    storeData() {
      this.clearCookies()

      this.$cookies.set("meas-i2c-1", this.i2c1)
      this.$cookies.set("meas-sensor-a-d-p1", this.analogDigitalP1)
      this.$cookies.set("meas-sensor-a-d-p2", this.analogDigitalP2)
      this.$cookies.set("meas-sensor-a-d-p3", this.analogDigitalP3)

      if (this.adc1TransformationIsVisible)
        this.$cookies.set("meas-sensor-a-d-p1-t", this.analogDigitalP1Transformation)

      if (this.adc2TransformationIsVisible)
        this.$cookies.set("meas-sensor-a-d-p2-t", this.analogDigitalP2Transformation)

      if (this.adc3TransformationIsVisible)
        this.$cookies.set("meas-sensor-a-d-p3-t", this.analogDigitalP2Transformation)

      this.requestGoNext()
    }
  }
}
</script>
