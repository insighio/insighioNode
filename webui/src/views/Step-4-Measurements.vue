<template>
  <div class="panel-body">
    <br />
    <!--div id="loader" class="loading loading-lg"></div-->
    <div class="container grid-lg">
      <div class="columns flex-centered">
        <div class="column col-xl-7 col-md-10 col-sm-12">
          <div class="form-group">
            <div class="columns">
              <SDivider label="Available measurements" />
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
                v-model:value="temperatureUnitIsCelsius"
                @update:value="temperatureUnitIsCelsius = $event"
                :valueOptions="temperatureUnitOptions"
              />
              <SSwitch label="GPS enabled" v-model:value="gpsEnabled" @update:value="gpsEnabled = $event" />

              <div v-if="gpsEnabled" style="margin: 20px" class="columns flex-centered col-12">
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

                <SSwitch
                  label="Discard measurements if no GPS fix"
                  v-model:value="gpsNoFixNoUpload"
                  @update:value="gpsNoFixNoUpload = $event"
                />
                <SSwitch
                  label="GPS only on boot"
                  v-model:value="gpsOnlyOnBoot"
                  @update:value="gpsOnlyOnBoot = $event"
                />
              </div>
              <br />

              <SDivider label="Explicit key-values" />
              <div class="accordion">
                <input type="checkbox" id="accordion-1" name="accordion-checkbox" hidden />
                <label class="accordion-header" for="accordion-1">
                  <i class="icon icon-arrow-right mr-1"></i>
                  Explicit key-values
                </label>
                <div class="accordion-body">
                  <div class="columns">
                    <div class="col-12">
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
                      <button class="btn btn-primary" @click="keyValuePairs.push({ key: '', value: '' })">
                        Add key-value pair
                      </button>
                    </div>
                  </div>
                  <br />
                </div>
              </div>
              <!--SDivider label="Explicit key-values" /-->

              <SDivider label="Shield Selection" />

              <div class="col-12">
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
              </div>
              <br />
              <div class="col-12" v-for="(tab, index) in tabs" :key="index" v-show="activeTab === tab.id">
                <br />
                <br />
                <ShieldScale v-if="tab.id === 'shield-scale-options'" />
                <ShieldDigitalAnalog v-else-if="tab.id === 'shield-dig-analog-options'" />
                <ShieldAdvind v-else-if="tab.id === 'shield-advind-options'" />
                <ShieldAccelerometer v-else-if="tab.id === 'shield-accel-options'" />
              </div>
              <br />
              <br />
            </div>
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
import ShieldScale from "./shields/ShieldScale.vue"
import ShieldDigitalAnalog from "./shields/ShieldDigitalAnalog.vue"
import ShieldAdvind from "./shields/ShieldAdvind.vue"
import ShieldAccelerometer from "./shields/ShieldAccelerometer.vue"

export default {
  name: "Step4Measurements",
  mixins: [CommonTools],
  components: {
    SSwitch,
    SInput,
    SDivider,
    SSelect,
    ShieldScale,
    ShieldDigitalAnalog,
    ShieldAdvind,
    ShieldAccelerometer
  },
  data() {
    return {
      ledEnabled: true,
      batteryStats: true,
      boardSense: true,
      boardStat: false,
      networkStat: true,
      otaEnabled: true,
      storeMeasIfFailedConn: true,
      temperatureUnitIsCelsius: true,
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
