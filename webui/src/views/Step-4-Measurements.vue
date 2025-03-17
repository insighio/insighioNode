<template>
  <div class="panel-body">
    <br />
    <div id="loader" class="loading loading-lg"></div>
    <div class="container grid-lg">
      <div class="columns flex-centered">
        <div class="column col-xl-7 col-md-10 col-sm-12">
          <div class="form-group">
            <div class="columns">
              <SDivider class="col-12" data-content="Available measurements" />
              <br />
              <SSwitch label="LED notifications" v-model:value="ledEnabled" @update:value="ledEnabled = $event" />
              <SSwitch label="Battery statistics" v-model:value="batteryStats" @update:value="batteryStats = $event" />
              <SSwitch
                label="Board humidity/temperature"
                v-model:value="boardSense"
                @update:value="boardSense = $event"
              />
              <SSwitch label="Network statistics" v-model:value="networkStat" @update:value="networkStat = $event" />
              <SSwitch label="OTA enabled" v-model:value="otaEnabled" @update:value="otaEnabled = $event" />
              <SSwitch
                label="Store measurements if failed connection"
                v-model:value="storeMeasIfFailedConn"
                @update:value="storeMeasIfFailedConn = $event"
              />
              <SSelect
                label="Temperature unit"
                v-model:value="temperatureUnitIsCelcius"
                @update:value="temperatureUnitIsCelcius = $event"
                :valueOptions="temperatureUnitOptions"
              />
              <SSwitch label="GPS enabled" v-model:value="gpsEnabled" @update:value="gpsEnabled = $event" />
              <SSwitch
                label="Discard measurements if no GPS fix"
                v-model:value="gpsNoFixNoUpload"
                @update:value="gpsNoFixNoUpload = $event"
              />
              <SSwitch label="GPS only on boot" v-m odel:value="gpsOnlyOnBoot" @update:value="gpsOnlyOnBoot = $event" />

              <br />
              <div id="address-gps" class="columns flex-centered col-12">
                <SInput
                  label="GPS Timeout (seconds)"
                  v-model:value="gpsTimeout"
                  type="number"
                  @update:value="gpsTimeout = $event"
                />
                <SInput
                  label="Min number of satellites"
                  v-model:value="gpsSatNum"
                  type="number"
                  @update:value="gpsSatNum = $event"
                />
              </div>
              <br />
              <div class="col-12">
                <div class="divider text-center" data-content="Device Selection"></div>
              </div>
              <br />
              <ul class="tab tab-block">
                <li
                  v-for="(tab, index) in tabs"
                  :key="index"
                  :class="['tab-item', { active: activeTab === tab.id }]"
                  @click="changeTab(tab.id)"
                >
                  <a class="pointer">{{ tab.label }}</a>
                </li>
              </ul>
              <br />
              <div v-for="(tab, index) in tabs" :key="index" v-show="activeTab === tab.id">
                <div v-if="tab.id === 'shield-scale-options'">
                  <SInput label="I2C #1" v-model:value="i2c1" />
                  <SInput label="I2C #2" v-model:value="i2c2" />
                  <SSwitch label="Weight Scale" v-model:value="scaleEnabled" @update:value="scaleEnabled = $event" />
                </div>
                <div v-else-if="tab.id === 'shield-dig-analog-options'">
                  <SInput label="I2C" v-model:value="i2c1" />
                  <SInput label="Analog / Digital P1" v-model:value="analogDigitalP1" />
                </div>
                <!-- Add other tab-specific content here -->
              </div>
              <br />
              <div class="form-group col-12">
                <div class="divider text-center" data-content="Explicit key-values"></div>
              </div>
              <br />
              <table class="table">
                <thead>
                  <tr>
                    <th>Key</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(pair, index) in keyValuePairs" :key="index">
                    <td>
                      <input type="text" v-model="pair.key" placeholder="key name" style="width: 100%" />
                    </td>
                    <td>
                      <input type="text" v-model="pair.value" placeholder="key value" style="width: 100%" />
                    </td>
                  </tr>
                </tbody>
              </table>
              <br />
            </div>
            <div class="column col-12">
              <button class="btn btn-primary float-right" @click="validateMyForm" style="margin-left: 30px">
                Save
              </button>
              <button class="btn btn-primary float-right" type="button" @click="requestGoBack">Back</button>
            </div>
            <br />
            <br />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"
import SSwitch from "@/components/SSwitch.vue"
import SInput from "@/components/SInput.vue"
import SDivider from "@/components/SDivider.vue"
import SSelect from "@/components/SSelect.vue"

export default {
  name: "Step4Measurements",
  mixins: [CommonTools],
  components: { SSwitch, SInput, SDivider, SSelect },
  data() {
    return {
      ledEnabled: true,
      batteryStats: true,
      boardSense: true,
      boardStat: false,
      networkStat: true,
      otaEnabled: true,
      storeMeasIfFailedConn: true,
      temperatureUnitIsCelcius: true,
      gpsEnabled: true,
      gpsTimeout: 120,
      gpsSatNum: 4,
      gpsNoFixNoUpload: false,
      gpsOnlyOnBoot: false,
      i2c1: "",
      i2c2: "",
      scaleEnabled: false,
      analogDigitalP1: "",
      keyValuePairs: [{ key: "", value: "" }],
      temperatureUnitOptions: [
        { value: true, label: "Celsius (C)" },
        { value: false, label: "Fahrenheit (F)" }
      ],
      tabs: [
        { id: "shield-scale-options", label: "Shield Digital/Scale" },
        { id: "shield-dig-analog-options", label: "Shield I2C/Analog" },
        { id: "shield-advind-options", label: "Shield SDI-12" },
        { id: "shield-accel-options", label: "Shield Accelerometer" }
      ],
      activeTab: "shield-scale-options"
    }
  },
  methods: {
    changeTab(tabId) {
      this.activeTab = tabId
    },
    validateMyForm() {
      // Add form validation and saving logic here
    },
    goBack() {
      // Add navigation logic here
    }
  }
}
</script>

<style scoped>
.measurements {
  /* Add your component styles here */
}
</style>
