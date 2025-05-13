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
    <SDivider label="MODBUS" />
    <div class="col-12 columns" style="border-color: #a0a0a0; border-width: 1px; border-style: solid; padding: 10px">
      <SDivider label="General Settings" />
      <SSelect
        label="Baud Rate"
        v-model:value="modbusConfig.baudRate"
        @update:value="modbusConfig.baudRate = $event"
        :valueOptions="modbusBaudRateOptions"
      />
      <SSelect
        label="Data Bits"
        v-model:value="modbusConfig.dataBits"
        @update:value="modbusConfig.dataBits = $event"
        :valueOptions="modbusDataBitsOptions"
      />
      <SSelect
        label="Stop Bits"
        v-model:value="modbusConfig.stopBits"
        @update:value="modbusConfig.stopBits = $event"
        :valueOptions="modbusStopBitsOptions"
      />
      <SSelect
        label="Parity"
        v-model:value="modbusConfig.parity"
        @update:value="modbusConfig.parity = $event"
        :valueOptions="modbusParityOptions"
      />
      <br />
      <SDivider label="Sensors" />
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
          <tr v-for="(row, index) in modbusSensors" :key="index">
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
              <select class="form-select" v-model="row.decimalDigits">
                <option v-for="opt in modbusDecimalDigits" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </td>

            <td><SSwitch v-model:value="row.mswFirst" /></td>
            <td><SSwitch v-model:value="row.littleEndian" /></td>
            <td>
              <button class="btn btn-primary" @click="modbusSensors.splice(index, 1)">
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
              <SSelect
                label="gain"
                v-model:value="adc.gain"
                @update:value="adc.gain = $event"
                :valueOptions="adsGainOptions"
                :tooltip="gain_tooltip"
              />
            </div>
            <div class="column col-2 col-mr-auto"></div>
            <div class="column col-1 col-mr-auto"></div>
            <div class="column col-9 col-mr-auto">
              <SInput
                label="formula"
                v-model:value="adc.formula"
                @update:value="adc.formula = $event"
                :tooltip="formula_tooltip"
              />
            </div>
            <div class="column col-2 col-mr-auto"></div>
          </div>
        </div>
      </div>
    </div>
    <SDivider label="Pulse Counter" />
    <div class="col-12" style="border-color: #a0a0a0; border-width: 1px; border-style: solid; padding: 10px">
      <div class="container" v-for="pc in pulseCounterConfig" :key="pc.id">
        <SSwitch :label="'Pulse Counter ' + pc.id" v-model:value="pc.enable" />
        <div v-if="pc.enable" class="col-12">
          <div class="form-group columns">
            <div class="column col-1 col-mr-auto"></div>
            <div class="column col-9 col-mr-auto">
              <SSwitch label="High Frequency" v-model:value="pc.highFreq" :colsLabel="4" :colsInput="8" />
              <SInput
                label="Pulse Counter formula"
                v-model:value="pc.formula"
                @update:value="pc.formula = $event"
                :tooltip="formula_tooltip"
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
import SSelect from "@/components/SSelect.vue"

export default {
  name: "ShieldEnviro",
  mixins: [CommonTools],
  components: { WebuiFooter, SInput, SDivider, SSwitch, SSelect },
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
        measCmd: "M",
        measSubCmd: ""
      },
      sdi12ConfigDefault: {
        warmupTimeMs: 1000
      },
      sdi12Config: {
        warmupTimeMs: 1000
      },
      adcDefaultConfig: [
        {
          id: 1,
          enabled: false,
          gain: 2,
          formula: "v"
        },
        {
          id: 2,
          enabled: false,
          gain: 2,
          formula: "v"
        },
        {
          id: 3,
          enabled: false,
          gain: 2,
          formula: "v"
        },
        {
          id: 4,
          enabled: false,
          gain: 2,
          formula: "v"
        }
      ],
      adcConfig: [],
      modbusSensors: [],
      modbusBaudRateOptions: [
        { value: 9600, label: "9600" },
        { value: 19200, label: "19200" },
        { value: 38400, label: "38400" },
        { value: 57600, label: "57600" },
        { value: 115200, label: "115200" }
      ],
      modbusDataBitsOptions: [
        { value: 7, label: "7" },
        { value: 8, label: "8" }
      ],
      modbusStopBitsOptions: [
        { value: 1, label: "1" },
        { value: 2, label: "2" }
      ],
      modbusParityOptions: [
        { value: null, label: "None" },
        { value: 2, label: "Even" },
        { value: 1, label: "Odd" }
      ],
      modbusConfigDefault: {
        baudRate: 9600,
        dataBits: 8,
        stopBits: 1,
        parity: null
      },
      modbusConfig: {},
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
        { value: 3, label: ".000" },
        { value: 4, label: ".0000" }
      ],
      //1 : 4.096V # 1x | 2 : 2.048V # 2x | 3 : 1.024V # 4x | 4 : 0.512V # 8x | 5 : 0.256V # 16x
      adsGainOptions: [
        { value: 1, label: "3.3V   # 1x" },
        { value: 2, label: "2.048V # 2x" },
        { value: 3, label: "1.024V # 4x" },
        { value: 4, label: "0.512V # 8x" },
        { value: 5, label: "0.256V # 16x" }
      ],
      pulseCounterDefaultConfig: [
        {
          id: 1,
          enabled: false,
          formula: "v",
          highFreq: false
        },
        {
          id: 2,
          enabled: false,
          formula: "v",
          highFreq: false
        }
      ],
      pulseCounterConfig: [],
      gain_tooltip:
        "defines the voltage range\nof the ADC input\nthe lower the voltage range\n the higher the precision",
      formula_tooltip: "python script to\ntransform raw value (v)\nfrom millivolt\nto meaningful value\nex: 2*v + v**2"
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

      this.modbusSensors =
        this.getJsonObjectFromCookies("meas-modbus") && this.getJsonObjectFromCookies("meas-modbus").sensors
          ? this.getJsonObjectFromCookies("meas-modbus").sensors
          : []

      this.modbusConfig =
        this.getJsonObjectFromCookies("meas-modbus") && this.getJsonObjectFromCookies("meas-modbus").config
          ? this.getJsonObjectFromCookies("meas-modbus").config
          : this.modbusConfigDefault

      this.adcConfig = this.getJsonObjectFromCookies("meas-adc")
        ? this.getJsonObjectFromCookies("meas-adc")
        : this.adcDefaultConfig
      this.pulseCounterConfig = this.getJsonObjectFromCookies("meas-pulseCounter")
        ? this.getJsonObjectFromCookies("meas-pulseCounter")
        : this.pulseCounterDefaultConfig
    },
    addSdi12Row() {
      this.sdi12Sensors.push({ ...this.sdi12DefaultRow })
    },
    addModbusRow() {
      this.modbusSensors.push({ ...this.modbusDefaultRow })
    },
    validateMyForm() {
      this.storeData()
    },
    clearCookies() {
      this.$cookies.remove("meas-sdi12")
      this.$cookies.remove("meas-modbus")
      this.$cookies.remove("meas-adc")
      this.$cookies.remove("meas-pulseCounter")
    },

    storeData() {
      this.clearCookies()

      this.$cookies.set("meas-sdi12", { sensors: this.sdi12Sensors, config: this.sdi12Config })
      this.$cookies.set("meas-modbus", { sensors: this.modbusSensors, config: this.modbusConfig })
      this.$cookies.set("meas-adc", this.adcConfig)
      this.$cookies.set("meas-pulseCounter", this.pulseCounterConfig)

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
