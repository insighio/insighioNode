<template>
  <div class="form-group columns">
    <SDivider label="SDI12" />
    <div class="col-12" style="border-color: #a0a0a0; border-width: 1px; border-style: solid; padding: 10px">
      <SDivider label="General Settings" />
      <SInput
        label="Warmup time (ms)"
        type="number"
        v-model:value="sdi12Config.warmupTimeMs"
        @update:value="sdi12Config.warmupTimeMs = $event"
      />
      <br />
      <SDivider label="Sensors" />
      <table class="table table-striped table-hover">
        <thead>
          <tr>
            <th>Index</th>
            <th>Sensor ID</th>
            <th>Command</th>
            <th>Sub Command</th>
            <th>Board Location</th>
            <th>
              <button :disabled="sdi12Sensors.length >= 10" class="btn btn-primary" @click="addSdi12Row">
                <i class="icon icon-plus"></i>
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in sdi12Sensors" :key="index">
            <td>{{ "SDI-12 n." + (index + 1) }}</td>
            <td>
              <select class="form-select" v-model="row.address">
                <option v-for="opt in sdi12sensorAddressOptions" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </td>
            <td>
              <select class="form-select" v-model="row.measCmd">
                <option v-for="opt in sdi12CommandOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </td>
            <td>
              <input type="text" class="form-input" maxlength="5" v-model="row.measSubCmd" />
            </td>
            <td>
              <button class="btn btn-primary" @click="sdi12Sensors.splice(index, 1)">
                <i class="icon icon-delete"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <!--div class="col-12">
      <button :disabled="sdi12Rows.length >= 10" class="btn btn-primary" @click="addSdi12Row">Add SDI-12 sensor</button>
    </div-->
    <SDivider label="4-20mA sensing" />
    <div class="col-12 columns">
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
    <SDivider label="Pulse Counter" />
    <div class="col-12">
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
      sdi12sensorAddressOptions: [],
      sdi12LocationOptions: [
        { value: "1", label: "SDI snr 1" },
        { value: "2", label: "SDI snr 2" }
      ],
      sdi12CommandOptions: [
        { value: "M", label: "M" },
        { value: "C", label: "C" },
        { value: "R", label: "R" },
        { value: "V", label: "V" },
        { value: "X", label: "X" }
      ],
      sdi12Sensors: [],
      sdi12DefaultRow: {
        address: 0,
        measCmd: "C",
        measSubCmd: "",
        boardLocation: "1"
      },
      sdi12ConfigDefault: {
        warmupTimeMs: 1000
      },
      sdi12Config: {
        warmupTimeMs: 1000
      },
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
      this.sdi12Sensors =
        this.getJsonObjectFromCookies("meas-sdi12") && this.getJsonObjectFromCookies("meas-sdi12").sensors
          ? this.getJsonObjectFromCookies("meas-sdi12").sensors
          : []

      this.sdi12Config =
        this.getJsonObjectFromCookies("meas-sdi12") && this.getJsonObjectFromCookies("meas-sdi12").config
          ? this.getJsonObjectFromCookies("meas-sdi12").config
          : this.sdi12ConfigDefault

      this.sens_4_20_num1_enable = this.strToJSValue(this.$cookies.get("meas-4-20-snsr-1-enable"), false)
      this.sens_4_20_num2_enable = this.strToJSValue(this.$cookies.get("meas-4-20-snsr-2-enable"), false)
      this.sens_4_20_num1_formula = this.$cookies.get("meas-4-20-snsr-1-formula")
        ? this.$cookies.get("meas-4-20-snsr-1-formula")
        : "v"
      this.sens_4_20_num2_formula = this.$cookies.get("meas-4-20-snsr-2-formula")
        ? this.$cookies.get("meas-4-20-snsr-2-formula")
        : "v"

      this.pulseCounterEnable = this.strToJSValue(this.$cookies.get("meas-pcnt-1-enable"), false)
      this.pulseCounterHighFreq = this.strToJSValue(this.$cookies.get("meas-pcnt-1-high-freq"), false)
      this.pulseCounterFormula = this.$cookies.get("meas-pcnt-1-formula")
        ? this.$cookies.get("meas-pcnt-1-formula")
        : "1"
    },
    addSdi12Row() {
      this.sdi12Sensors.push({ ...this.sdi12DefaultRow })
    },
    validateMyForm() {
      this.storeData()
    },
    clearCookies() {
      this.$cookies.remove("meas-sdi12")
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

      this.$cookies.set("meas-sdi12", { sensors: this.sdi12Sensors, config: this.sdi12Config })

      this.$cookies.set("meas-4-20-snsr-1-enable", this.boolToPyStr(this.sens_4_20_num1_enable))
      this.$cookies.set("meas-4-20-snsr-2-enable", this.boolToPyStr(this.sens_4_20_num2_enable))
      this.$cookies.set("meas-4-20-snsr-1-formula", this.sens_4_20_num1_formula)
      this.$cookies.set("meas-4-20-snsr-2-formula", this.sens_4_20_num2_formula)

      this.$cookies.set("meas-pcnt-1-enable", this.boolToPyStr(this.pulseCounterEnable))
      this.$cookies.set("meas-pcnt-1-formula", this.pulseCounterFormula)
      this.$cookies.set("meas-pcnt-1-high-freq", this.boolToPyStr(this.pulseCounterHighFreq))

      this.requestGoNext()
    }
  },
  mounted() {
    this.sdi12sensorAddressOptions = []
    for (let i = 0; i <= 9; i++) {
      this.sdi12sensorAddressOptions.push({ value: i, label: i.toString() })
    }
    // Add your mounted logic here
    this.initializeValues()
  }
}
</script>
