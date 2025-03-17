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
  methods: {
    // Add your component methods here
  },
  computed: {
    // Add your computed properties here
  },
  mounted() {
    // Add your mounted logic here
  }
}
</script>

<style scoped>
.network {
  /* Add your component styles here */
}
</style>
