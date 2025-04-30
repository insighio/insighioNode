<template>
  <div class="form-group columns">
    <SDivider label="SDI12" />
    <div class="col-12" style="border-color: #a0a0a0; border-width: 1px; border-style: solid; padding: 10px">
      <table class="table table-striped table-hover">
        <thead>
          <tr>
            <th>Index</th>
            <th>Sensor ID</th>
            <th>Command</th>
            <th>
              <button :disabled="sdi12Rows.length >= 10" class="btn btn-primary" @click="addSdi12Row">
                <i class="icon icon-plus"></i>
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in sdi12Rows" :key="index">
            <td>{{ "SDI-12 n." + (index + 1) }}</td>
            <td>
              <select class="form-select" v-model="row.sensorAddress">
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
              <button class="btn btn-primary" @click="sdi12Rows.splice(index, 1)">
                <i class="icon icon-delete"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <br />
      <br />

      <SInput
        label="Warmup time (ms)"
        type="number"
        v-model:value="sdi12WarmupTimeMs"
        @update:value="sdi12WarmupTimeMs = $event"
      />
    </div>
    <SDivider label="MODBUS" />
    <div class="col-12 columns" style="border-color: #a0a0a0; border-width: 1px; border-style: solid; padding: 10px">
      <table class="table table-striped table-hover">
        <thead>
          <tr>
            <th>Slave Addr</th>
            <th>Register</th>
            <th>Type</th>
            <th>Format</th>
            <th>Factor</th>
            <th>Decimal Digits</th>
            <th>MSW First</th>
            <th>Little Endian</th>
            <th>
              <button class="btn btn-primary" @click="addModbusRow">
                <i class="icon icon-plus"></i>
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in modbusConfig" :key="index">
            <td><input type="number" class="form-input" v-model="row.slaveAddress" /></td>
            <td><input type="number" class="form-input" v-model="row.register" /></td>
            <td>
              <select class="form-select" v-model="row.type">
                <option v-for="opt in modbusSupportedTypes" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </td>
            <td>
              <select class="form-select" v-model="row.format">
                <option v-for="opt in modbusSupportedFormats" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </td>

            <td><input type="number" class="form-input" step="0.000001" v-model="row.factor" /></td>
            <td>
              <select :disabled="row.format !== 'float'" class="form-select" v-model="row.decimalDigits">
                <option v-for="opt in modbusDecimalDigits" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </td>

            <td><SSwitch v-model:value="row.mswFirst" /></td>
            <td><SSwitch v-model:value="row.littleEndian" /></td>
            <td>
              <button class="btn btn-primary" @click="modbusConfig.splice(index, 1)">
                <i class="icon icon-delete"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <br />
      <br />
    </div>
    <SDivider label="ADC" />
    <div class="col-12 columns" style="border-color: #a0a0a0; border-width: 1px; border-style: solid; padding: 10px">
      <div class="container" v-for="adc in adcConfig" :key="adc.id">
        <SSwitch :label="'Analog Sensor' + adc.id" v-model:value="adc.enabled" />

        <div v-if="adc.enabled" class="col-12">
          <div class="form-group columns">
            <div class="column col-1 col-mr-auto"></div>
            <div class="column col-9 col-mr-auto">
              <SInput
                label="formula"
                v-model:value="adc.formula"
                @update:value="adc.formula = $event"
                :tooltip="tooltip"
              />
            </div>
            <div class="column col-2 col-mr-auto"></div>
          </div>
        </div>
      </div>
    </div>
    <SDivider label="Pulse Counter" />
    <div class="col-12" style="border-color: #a0a0a0; border-width: 1px; border-style: solid; padding: 10px">
      <div class="container">
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
  name: "ShieldEnviro",
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
        { value: "C", label: "C" }
      ],
      sdi12Rows: [],
      sdi12DefaultRow: {
        sensorAddress: 1,
        measCmd: "M"
      },
      sdi12WarmupTimeMs: 1000,
      adcConfig: [
        {
          id: 1,
          enabled: false,
          formula: "v"
        },
        {
          id: 2,
          enabled: false,
          formula: "v"
        },
        {
          id: 3,
          enabled: false,
          formula: "v"
        },
        {
          id: 4,
          enabled: false,
          formula: "v"
        }
      ],
      modbusConfig: [],
      modbusDefaultRow: {
        slaveAddress: 0,
        register: 0,
        type: 3,
        format: "uint16",
        factor: 1,
        decimalDigits: 0,
        mswFirst: true,
        littleEndian: false
      },
      modbusSupportedTypes: [
        // { value: 1, label: "Coil" },
        // { value: 2, label: "Discrete Input" },
        { value: 3, label: "Holding Register" },
        { value: 4, label: "Input Register" }
      ],
      modbusSupportedFormats: [
        // { value: "bit", label: "Boolean (1b)" },
        { value: "int16", label: "Signed Int (16b)" },
        { value: "uint16", label: "Unsigned Int (16b)" },
        { value: "int32", label: "Signed Int (32b)" },
        { value: "uint32", label: "Unsigned Int (32b)" },
        { value: "float", label: "Single Precision Float (32b)" }
      ],
      modbusDecimalDigits: [
        { value: 0, label: "-" },
        { value: 1, label: ".0" },
        { value: 2, label: ".00" },
        { value: 3, label: ".000" }
      ],

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
      this.sdi12Rows = []
      for (let i = 1; i <= 10; ++i) {
        const rowEnabled = this.strToJSValue(this.$cookies.get("meas-sdi-" + i + "-enabled"))
        const rowLoc = this.$cookies.get("meas-sdi-" + i + "-loc")
        const rowAddress = this.$cookies.get("meas-sdi-" + i + "-address")

        if (
          rowEnabled === undefined ||
          rowEnabled === null ||
          !rowLoc ||
          rowAddress === undefined ||
          rowAddress === null
        ) {
          continue
        }
        this.sdi12Rows.push({ sensorAddress: rowAddress, active: rowEnabled })
      }

      // if (this.sdi12Rows.length === 0) {
      //   this.sdi12Rows.push({ sensorAddress: 1, boardLocation: "1", measCmd: "M" })
      // }

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
      this.pulseCounterHighFreq = this.strToJSValue(this.$cookies.get("meas-pcnt-1-high-freq"), false)
      this.pulseCounterFormula = this.$cookies.get("meas-pcnt-1-formula")
        ? this.$cookies.get("meas-pcnt-1-formula")
        : "1"
    },
    addSdi12Row() {
      if (this.sdi12Rows.length < 10) this.sdi12Rows.push({ ...this.sdi12DefaultRow })
    },
    addModbusRow() {
      this.modbusConfig.push({ ...this.modbusDefaultRow })
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
        this.$cookies.set("meas-sdi-" + config_index + "-address", this.sdi12Rows[i].sensorAddress)
        this.$cookies.set("meas-sdi-" + config_index + "-loc", this.sdi12Rows[i].boardLocation)
      }

      this.$cookies.set("meas-4-20-snsr-1-enable", this.boolToPyStr(this.sens_4_20_num1_enable))
      this.$cookies.set("meas-4-20-snsr-2-enable", this.boolToPyStr(this.sens_4_20_num2_enable))
      this.$cookies.set("meas-4-20-snsr-1-formula", this.sens_4_20_num1_formula)
      this.$cookies.set("meas-4-20-snsr-2-formula", this.sens_4_20_num2_formula)

      this.$cookies.set("meas-sdi-warmup-time", this.sdi12WarmupTimeMs)

      this.$cookies.set("meas-pcnt-1-enable", this.boolToPyStr(this.pulseCounterEnable))
      this.$cookies.set("meas-pcnt-1-formula", this.pulseCounterFormula)
      this.$cookies.set("meas-pcnt-1-high-freq", this.boolToPyStr(this.pulseCounterHighFreq))

      this.requestGoNext()
    }
  },
  mounted() {
    this.sdi12sensorAddressOptions = []
    for (let i = 1; i <= 10; i++) {
      this.sdi12sensorAddressOptions.push({ value: i, label: i.toString() })
    }
    // Add your mounted logic here
    this.initializeValues()
  }
}
</script>
