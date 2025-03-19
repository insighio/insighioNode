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
      this.requestGoNext()
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
      disableNavigationButtons()
      this.clearCookies()

      this.$cookies.set("meas-led-enabled", this.boolElemToPyStr("input-led-enabled"))
      this.$cookies.set("meas-battery-stat", this.boolElemToPyStr("input-battery"))
      this.$cookies.set("meas-board-sense", this.boolElemToPyStr("input-board-sense"))
      this.$cookies.set("meas-board-stat", this.boolElemToPyStr("input-board-stat"))
      this.$cookies.set("meas-network-stat", this.boolElemToPyStr("input-network"))
      this.$cookies.set("system-enable-ota", this.boolElemToPyStr("input-ota"))
      this.$cookies.set("meas-gps-enabled", this.boolElemToPyStr("input-gps-enable"))

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
      this.$cookies.set("meas-gps-no-fix-no-upload", this.boolElemToPyStr("input-gps-no-fix-no-upload"))
      this.$cookies.set("meas-gps-only-on-boot", this.boolElemToPyStr("input-gps-only-on-boot"))

      this.$cookies.set("store-meas-if-failed-conn", this.boolElemToPyStr("input-store-meas-if-failed-conn"))

      this.$cookies.set("meas-keyvalue", getKeyValuePairs())

      if (elementIsVisible("shield-advind-options")) {
        this.$cookies.set("selected-shield", shieldNamePerTab["shield-advind-options"])

        for (let i = 1; i < 11; ++i) {
          setSDI12Cookie(i)
        }

        this.$cookies.set("meas-4-20-snsr-1-enable", this.boolElemToPyStr("ins-esp-gen-4-20-snsr-1-enable"))
        this.$cookies.set("meas-4-20-snsr-2-enable", this.boolElemToPyStr("ins-esp-gen-4-20-snsr-2-enable"))
        this.$cookies.set("meas-4-20-snsr-1-formula", document.getElementById("ins-esp-gen-4-20-snsr-1-formula").value)
        this.$cookies.set("meas-4-20-snsr-2-formula", document.getElementById("ins-esp-gen-4-20-snsr-2-formula").value)

        this.$cookies.set("meas-sdi-warmup-time", document.getElementById("input-gen-sdi12-warmup-time").value)

        this.$cookies.set("meas-pcnt-1-enable", this.boolElemToPyStr("ins-esp-gen-pcnt-1-enable"))
        ///this.$cookies.set('meas-pcnt-1-cnt-on-rising', document.getElementById('ins-esp-gen-pcnt-1-cnt-on').value === "rising")
        this.$cookies.set("meas-pcnt-1-formula", document.getElementById("ins-esp-gen-pcnt-1-formula").value)
        this.$cookies.set("meas-pcnt-1-high-freq", this.boolElemToPyStr("ins-esp-gen-pcnt-1-high-freq"))

        redirectoToMeasurementNaming()
      } else if (elementIsVisible("shield-scale-options")) {
        this.$cookies.set("selected-shield", shieldNamePerTab["shield-scale-options"])
        this.$cookies.set("meas-i2c-1", document.getElementById("input-i2c-1").value)
        this.$cookies.set("meas-i2c-2", document.getElementById("input-i2c-2").value)
        this.$cookies.set("meas-sensor-a-d-p1", document.getElementById("input-sensor-a-d-p1").value)
        this.$cookies.set("meas-scale-enabled", this.boolElemToPyStr("input-scale-enabled"))
        this.$cookies.set("meas-scale-monitoring-enabled", this.boolElemToPyStr("input-scale-monitoring"))

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
