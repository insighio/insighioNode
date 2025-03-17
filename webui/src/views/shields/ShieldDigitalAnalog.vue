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
    <SInput label="Analog / Digital P1" v-model:value="analogDigitalP1" />
    <div id="input-s1-sensor-a-d-p1-trans-div" class="col-12" style="display: block">
      <br />
      <div class="form-group columns">
        <div class="column col-1 col-mr-auto"></div>
        <div class="col-3 col-sm-12">
          <label class="form-label" for="measurements"
            >transformation
            <button
              class="btn btn-link tooltip"
              data-tooltip="python script to&#xa;transform raw Value (v)&#xa;from millivolt&#xa;to meaningful value&#xa;ex: 2*v + v**2"
            >
              <i class="icon icon-flag"></i>
            </button>
          </label>
        </div>
        <div class="col-6 col-sm-12">
          <input class="form-input constr-field" id="input-s1-sensor-a-d-p1-t" />
        </div>
        <div class="column col-2 col-mr-auto"></div>
      </div>
    </div>
    <br />
    <div class="col-4 col-lg-6">
      <label class="form-label" for="measurements">Analog / Digital P2</label>
    </div>
    <div class="col-8 col-lg-6">
      <select class="form-select" id="input-s1-sensor-a-d-p2" onchange="selectionChanged(this)"></select>
    </div>
    <div id="input-s1-sensor-a-d-p2-trans-div" class="col-12" style="display: none">
      <br />
      <div class="form-group columns">
        <div class="column col-1 col-mr-auto"></div>
        <div class="col-3 col-sm-12">
          <label class="form-label" for="measurements"
            >transformation
            <button
              class="btn btn-link tooltip"
              data-tooltip="python script to&#xa;transform raw value (v)&#xa;from millivolt&#xa;to meaningful value&#xa;ex: 2*v + v**2"
            >
              <i class="icon icon-flag"></i>
            </button>
          </label>
        </div>
        <div class="col-6 col-sm-12">
          <input class="form-input constr-field" id="input-s1-sensor-a-d-p2-t" />
        </div>
        <div class="column col-2 col-mr-auto"></div>
      </div>
    </div>
    <br />
    <br />
    <div class="col-4 col-lg-6">
      <label class="form-label" for="measurements">Analog / Digital P3</label>
    </div>
    <div class="col-8 col-lg-6">
      <select class="form-select" id="input-s1-sensor-a-d-p3" onchange="selectionChanged(this)"></select>
    </div>
    <div id="input-s1-sensor-a-d-p3-trans-div" class="col-12" style="display: none">
      <br />
      <div class="form-group columns">
        <div class="column col-1 col-mr-auto"></div>
        <div class="col-3 col-sm-12">
          <label class="form-label" for="measurements"
            >transformation
            <button
              class="btn btn-link tooltip"
              data-tooltip="python script to&#xa;transform raw value (v)&#xa;from millivolt&#xa;to meaningful value&#xa;ex: 2*v + v**2"
            >
              <i class="icon icon-flag"></i>
            </button>
          </label>
        </div>
        <div class="col-6 col-sm-12">
          <input class="form-input constr-field" id="input-s1-sensor-a-d-p3-t" />
        </div>
        <div class="column col-2 col-mr-auto"></div>
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
  components: { SInput, SSelect, WebuiFooter },
  data() {
    return {
      // Add your component data here
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
