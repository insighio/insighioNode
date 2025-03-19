<template>
  <div class="form-group columns">
    <div class="col-12">
      <table class="table table-striped table-hover">
        <thead>
          <tr>
            <th>Index</th>
            <th>Sensor ID</th>
            <th>Board Location</th>
            <th>Active</th>
          </tr>
        </thead>
        <tbody id="option-sdi12-table-rows">
          <tr v-for="(row, index) in sdi12Rows" :key="index">
            <td>{{ "SDI-12 n." + (index + 1) }}</td>
            <td>
              <select class="form-select" v-model="row.sensorId">
                <option v-for="opt in sdi12SensorIdOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </td>
            <td>
              <select class="form-select" v-model="row.boardLocation">
                <option v-for="opt in sdi12LocationOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </td>
            <td>
              <label class="form-switch">
                <input type="checkbox" v-model="row.active" />
                <i class="form-icon"></i>
              </label>
            </td>
          </tr>
        </tbody>
      </table>

      <br />
    </div>
    <div class="col-12">
      <button :disabled="sdi12Rows.length >= 10" class="btn btn-primary" @click="addSdi12Row">Add SDI-12 sensor</button>
    </div>
    <SInput
      label="Warmup time (ms)"
      type="number"
      v-model:value="sdi12WarmupTimeMs"
      @update:value="sdi12WarmupTimeMs = $event"
    />
    <div class="col-12 columns">
      <SDivider label="4-20mA sensing" />
      <SSwitch label="Sensor 1 enable" v-model:value="sens_4_20_num1_enable" />

      <div v-if="sens_4_20_num1_enable" class="col-12">
        <div class="form-group columns">
          <div class="column col-1 col-mr-auto"></div>
          <div class="column col-9 col-mr-auto">
            <SInput
              label="Sensor 1 formula"
              v-model:value="sens_4_20_num1_formula"
              @update:value="sens_4_20_num1_formula = $event"
              :tooltip="tooltip"
            />
          </div>
          <div class="column col-2 col-mr-auto"></div>
        </div>
      </div>
      <SSwitch label="Sensor 2 enable" v-model:value="sens_4_20_num2_enable" />
      <div v-if="sens_4_20_num2_enable" class="col-12">
        <div class="form-group columns">
          <div class="column col-1 col-mr-auto"></div>
          <div class="column col-9 col-mr-auto">
            <SInput
              label="Sensor 2 formula"
              v-model:value="sens_4_20_num2_formula"
              @update:value="sens_4_20_num2_formula = $event"
              :tooltip="tooltip"
            />
          </div>
          <div class="column col-2 col-mr-auto"></div>
        </div>
      </div>
    </div>
    <div class="col-12">
      <SDivider label="Pulse Counter" />
      <SSwitch label="Pulse Counter enable" v-model:value="pulseCounterEnable" />
      <div v-if="pulseCounterEnable" class="col-12">
        <div class="form-group columns">
          <div class="column col-1 col-mr-auto"></div>
          <div class="column col-9 col-mr-auto">
            <SSwitch label="High Frequency" v-model:value="pulseCounterHighFreq" :colsLabel="4" :colsInput="8" />
            <SInput
              label="Pulse Counter formula"
              v-model:value="pulseCounterFormula"
              @update:value="pulseCounterFormula = $event"
              :tooltip="tooltip"
            />
          </div>
          <div class="column col-2 col-mr-auto"></div>
        </div>
      </div>
    </div>
    <br />
    <br />
    <WebuiFooter @savePressed="validateMyForm" @backPressed="requestGoBack" />
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"
import WebuiFooter from "@/components/WebuiFooter.vue"
import SInput from "@/components/SInput.vue"
import SDivider from "@/components/SDivider.vue"
import SSwitch from "@/components/SSwitch.vue"

export default {
  name: "ShieldAdvind",
  mixins: [CommonTools],
  components: { WebuiFooter, SInput, SDivider, SSwitch },
  data() {
    return {
      // Add your component data here
      sdi12SensorIdOptions: [],
      sdi12LocationOptions: [
        { value: "1", label: "SDI snr 1" },
        { value: "2", label: "SDI snr 2" }
      ],
      sdi12Rows: [],
      sdi12WarmupTimeMs: 1000,
      sens_4_20_num1_enable: false,
      sens_4_20_num1_formula: "v",
      sens_4_20_num2_enable: false,
      sens_4_20_num2_formula: "v",
      pulseCounterEnable: false,
      pulseCounterHighFreq: false,
      pulseCounterFormula: "v",
      tooltip: "python script to\ntransform raw value (v)\nfrom millivolt\nto meaningful value\nex: 2*v + v**2"
    }
  },
  methods: {
    initializeValues() {
      for (let i = 1; i <= 10; ++i) {
        const rowEnabled = this.strToJSValue(this.$cookies.get("meas-sdi-" + i + "-enabled"))
        const rowLoc = this.$cookies.get("meas-sdi-" + i + "-loc")
        const rowAddress = this.$cookies.get("meas-sdi-" + i + "-address")

        this.sdi12Rows.push({ sensorId: rowAddress, boardLocation: rowLoc, active: rowEnabled })
      }

      this.sdi12WarmupTimeMs = this.$cookies.get("meas-sdi-warmup-time")
        ? this.$cookies.get("meas-sdi-warmup-time")
        : 1000
      this.sens_4_20_num1_enable = this.strToJSValue(this.$cookies.get("meas-4-20-snsr-1-enable"), false)
      this.sens_4_20_num2_enable = this.strToJSValue(this.$cookies.get("meas-4-20-snsr-2-enable"), false)
      this.sens_4_20_num1_formula = this.$cookies.get("meas-4-20-snsr-1-formula")
        ? this.$cookies.get("meas-4-20-snsr-1-formula")
        : "v"
      this.sens_4_20_num2_formula = this.$cookies.get("meas-4-20-snsr-2-formula")
        ? this.$cookies.get("meas-4-20-snsr-2-formula")
        : "v"
      this.pulseCounterEnable = this.strToJSValue(this.$cookies.get("meas-pcnt-1-enable"), false)
      this.pulseCounterHighFreq = this.strToJSValue(this.$cookies.get("meas-pcnt-1-high-freq"), true)
      this.pulseCounterFormula = this.$cookies.get("meas-pcnt-1-formula")
        ? this.$cookies.get("meas-pcnt-1-formula")
        : "1"
    },
    addSdi12Row() {
      if (this.sdi12Rows.length < 10) this.sdi12Rows.push({ sensorId: 1, boardLocation: "1", active: true })
    },
    validateMyForm() {
      this.storeData()
    },
    clearCookies() {
      this.$cookies.remove("meas-4-20-snsr-1-enable")
      this.$cookies.remove("meas-4-20-snsr-2-enable")
      this.$cookies.remove("meas-4-20-snsr-1-formula")
      this.$cookies.remove("meas-4-20-snsr-2-formula")
      this.$cookies.remove("meas-pcnt-1-enable")
      this.$cookies.remove("meas-pcnt-1-cnt-on-rising")
      this.$cookies.remove("meas-pcnt-1-formula")
      this.$cookies.remove("meas-pcnt-1-high-freq")

      this.$cookies.remove("meas-sdi-warmup-time")

      for (let i = 1; i < 11; ++i) {
        this.$cookies.remove("meas-sdi-" + i + "-enabled")
        this.$cookies.remove("meas-sdi-" + i + "-address")
        this.$cookies.remove("meas-sdi-" + i + "-loc")
      }
    },

    storeData() {
      this.clearCookies()

      for (let i = 0; i < this.sdi12Rows.length; ++i) {
        const config_index = i + 1
        this.$cookies.set("meas-sdi-" + config_index + "-enabled", this.boolToPyStr(this.sdi12Rows[i].active))
        this.$cookies.set("meas-sdi-" + config_index + "-address", this.sdi12Rows[i].sensorId)
        this.$cookies.set("meas-sdi-" + config_index + "-loc", this.sdi12Rows[i].boardLocation)
      }

      this.$cookies.set("meas-4-20-snsr-1-enable", this.boolToPyStr(this.sens_4_20_num1_enable))
      this.$cookies.set("meas-4-20-snsr-2-enable", this.boolToPyStr(this.sens_4_20_num2_enable))
      this.$cookies.set("meas-4-20-snsr-1-formula", this.sens_4_20_num1_formula)
      this.$cookies.set("meas-4-20-snsr-2-formula", this.sens_4_20_num2_formula)

      this.$cookies.set("meas-sdi-warmup-time", this.sdi12WarmupTimeMs)

      this.$cookies.set("meas-pcnt-1-enable", this.boolToPyStr)
      ///this.$cookies.set('meas-pcnt-1-cnt-on-rising', document.getElementById('ins-esp-gen-pcnt-1-cnt-on').value === "rising")
      this.$cookies.set("meas-pcnt-1-formula", this.pulseCounterFormula)
      this.$cookies.set("meas-pcnt-1-high-freq", this.boolToPyStr(this.pulseCounterHighFreq))

      this.requestGoNext()
    }
  },
  computed: {
    // Add your computed properties here
  },
  mounted() {
    this.sdi12SensorIdOptions = []
    for (let i = 1; i <= 10; i++) {
      this.sdi12SensorIdOptions.push({ value: i, label: i.toString() })
    }
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
