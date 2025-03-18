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
