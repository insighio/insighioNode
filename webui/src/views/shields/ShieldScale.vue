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
    <div v-if="scaleEnabled" class="columns col-12" style="padding-right: 0px; padding-left: 0px">
      <div class="col-4 col-sm-12">
        <label class="form-label"></label>
      </div>
      <div class="col-8 col-sm-12">
        <button class="btn btn-primary" @click="startCalibration()" style="margin-left: 30px">Calibrate</button>
      </div>
      <br />
      <br />
    </div>
    <SSwitch
      label="[Debug] Enable Scale Sensor Monitoring"
      v-model:value="scaleMonitoring"
      @update:value="scaleMonitoring = $event"
      :colsLabel="4"
      :colsInput="8"
    />
    <br />
    <br />
    <WebuiFooter @savePressed="validateMyForm" @backPressed="requestGoBack" />

    <!-- Wizard Dialog -->
    <div v-if="showWizard" class="modal active">
      <div class="modal-overlay" @click="closeWizard"></div>
      <div class="modal-container">
        <div class="modal-header">
          <button class="btn btn-clear float-right" @click="closeWizard"></button>
          <div class="modal-title h5">Calibration Wizard</div>
        </div>
        <div class="modal-body">
          <div class="empty" v-if="currentStep === 1">
            <!-- Step 1: Idle Calibration -->
            <p class="empty-title h5">Weight Scale Calibration</p>
            <p class="empty-subtitle">
              Ready for weight scale calibration. Remove any weight from the scale and hit
              <span class="text-bold">Measure</span> button to save the idle state of the scale.
            </p>
            <div class="empty-action">
              <div class="column col-12">
                <button style="margin: 0px 5px 0px 5px" class="btn btn-primary" @click="closeWizard">Back</button>
                <button style="margin: 0px 5px 0px 5px" class="btn btn-primary" @click="goToNextStep">Measure</button>
              </div>
            </div>
          </div>
          <div class="empty" v-if="currentStep === 2">
            <!-- Step 2: Reference Weight -->
            <p class="empty-title h5">Weight Scale Calibration</p>
            <p class="empty-subtitle">
              Idle value (offset) is:
              <span class="text-bold"
                ><div v-if="isLoading" class="loading"></div>
                <progress
                  class="progress"
                  :value="progressValue"
                  max="30"
                  style="display: none; margin: auto"
                ></progress
                >{{ scaleOffset }}</span
              >
            </p>
            <p class="empty-subtitle">
              Place your reference weight on the scale, fill its exact weight in grams at the following field and press
              <span class="text-bold">Measure</span> to complete calibration.
            </p>
            <div class="columns">
              <div class="col-3 col-sm-12 col-ml-auto">
                <label class="form-label p-centered" for="input-ref-weight">Reference Weight (g)</label>
              </div>
              <div class="col-3 col-sm-12 col-mr-auto">
                <input class="form-input p-centered" type="number" v-model="referenceWeight" style="width: 300px" />
              </div>
            </div>
            <div class="empty-action">
              <button
                :disabled="isLoading"
                style="margin: 0px 5px 0px 5px"
                class="btn btn-primary"
                @click="goToPreviousStep"
              >
                Back
              </button>
              <button
                :disabled="isLoading"
                style="margin: 0px 5px 0px 5px"
                class="btn btn-primary"
                @click="goToNextStep"
              >
                Measure
              </button>
            </div>
          </div>
          <div class="empty" v-if="currentStep === 3">
            <!-- Step 3: Calibration Results -->
            <p class="empty-title h5">Weight Scale Calibration</p>
            <p class="empty-subtitle">
              Offset: <span class="text-bold">{{ scaleOffset }}</span>
            </p>
            <p class="empty-subtitle">
              Measured reference weight: <span class="text-bold">{{ measuredRefWeight }}</span>
            </p>
            <p class="empty-subtitle">
              Scale: <span class="text-bold">{{ scaleScale }}</span>
            </p>
            <p class="empty-subtitle">
              Current Weight(g):
              <span class="text-bold"
                ><progress
                  class="progress"
                  :value="progressValue"
                  max="30"
                  style="display: none; margin: auto"
                ></progress
                >{{ currentWeight }}</span
              >
            </p>
            <div class="empty-action">
              <button
                class="btn btn-primary"
                :disabled="isLoading"
                style="margin-top: 5px; margin-right: 5px"
                @click="recalibrate()"
              >
                Recalibrate
              </button>
              <button
                class="btn btn-primary"
                :disabled="isLoading"
                style="margin-top: 5px; margin-right: 5px"
                @click="requestMeasure()"
              >
                Measure
              </button>
              <button
                class="btn btn-primary"
                :disabled="isLoading"
                style="margin-top: 5px; margin-right: 5px"
                @click="requestTare()"
              >
                Tare
              </button>
              <button
                class="btn btn-primary"
                :disabled="isLoading"
                style="margin-top: 5px; margin-right: 5px"
                @click="goToPreviousStep()"
              >
                Back
              </button>
              <button
                class="btn btn-primary"
                :disabled="isLoading"
                style="margin-top: 5px; margin-right: 5px"
                @click="saveCalibration()"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
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
      scaleMonitoring: false,
      showWizard: false,
      currentStep: 1,
      referenceWeight: null,
      measuredRefWeight: null,
      scaleOffset: null,
      scaleScale: null,
      currentWeight: null,
      isLoading: false,
      progressValue: 0,
      progressInterval: null
    }
  },
  mounted() {
    this.initializeValues()
  },
  methods: {
    initializeValues() {
      // Add initialization logic here
      this.i2c1 = this.strToJSValue(this.$cookies.get("meas-i2c-1"), "disabled")
      this.i2c2 = this.strToJSValue(this.$cookies.get("meas-i2c-2"), "disabled")
      this.adcP1 = this.strToJSValue(this.$cookies.get("meas-sensor-a-d-p1"), "disabled")
      this.scaleEnabled = this.strToJSValue(this.$cookies.get("meas-scale-enabled"), false)
      this.scaleMonitoring = this.strToJSValue(this.$cookies.get("meas-scale-monitoring-enabled"), false)
      this.scaleOffset = this.$cookies.get("meas-scale-offset")
      this.scaleScale = this.$cookies.get("meas-scale-scale")
    },
    // Add your component methods here
    validateMyForm() {
      this.requestGoNext()
    },

    clearCookies() {
      this.$cookies.remove("meas-i2c-1")
      this.$cookies.remove("meas-i2c-2")
      this.$cookies.remove("meas-sensor-a-d-p1")
      this.$cookies.remove("meas-sensor-a-d-p1-t")
      this.$cookies.remove("meas-sensor-scale-enabled")
      this.$cookies.remove("meas-scale-monitoring-enabled")
      this.$cookies.remove("meas-scale-offset")
      this.$cookies.remove("meas-scale-scale")
    },

    storeData() {
      this.clearCookies()

      this.$cookies.set("meas-i2c-1", this.i2c1)
      this.$cookies.set("meas-i2c-2", this.i2c2)
      this.$cookies.set("meas-sensor-a-d-p1", this.adcP1)
      this.$cookies.set("meas-scale-enabled", this.strToJSValue(this.scaleEnabled))
      this.$cookies.set("meas-scale-monitoring-enabled", this.strToJSValue(this.scaleMonitoring))

      if (this.scaleEnabled) {
        this.$cookies.set("meas-scale-scale", this.scaleScale)
        this.$cookies.set("meas-scale-offset", this.scaleOffset)
      } else {
        this.$cookies.set("meas-scale-scale", 1)
        this.$cookies.set("meas-scale-offset", 0)
      }

      this.requestGoNext()
    },
    startProgressAnimation() {
      this.isLoading = true
      this.progressValue = 0
      this.progressInterval = setInterval(() => {
        this.progressValue += 1
        if (this.progressValue >= 30) {
          clearInterval(this.progressInterval)
          this.isLoading = false
        }
      }, 500)
    },

    stopProgressAnimation() {
      clearInterval(this.progressInterval)
      this.isLoading = false
    },
    startCalibration() {
      this.showWizard = true
      this.currentStep = 1
    },
    closeWizard() {
      this.showWizard = false
    },
    goToNextStep() {
      if (this.currentStep === 1) {
        this.getScaleOffset()
      } else if (this.currentStep === 2) {
        // Simulate measuring reference weight
        this.measuredRefWeight = this.referenceWeight // Replace with actual logic
        this.scale = 1 // Replace with actual logic
      }
      this.currentStep++
    },
    getScaleOffset() {
      // Simulate saving idle weight
      this.startProgressAnimation()
      fetch("/raw-weight-idle?board=" + this.$cookies.get("hw-module"))
        .then((response) => {
          return response.json()
        })
        .then((data) => {
          this.scaleOffset = data.raw

          this.stopProgressAnimation()
        })
        .catch((err) => {
          this.stopProgressAnimation()
        })
    },
    calculateScaleMultiplier() {
      this.startProgressAnimation()
      fetch("/raw-weight-idle?board=" + this.$cookies.get("selected-board"))
        .then((response) => {
          return response.json()
        })
        .then(function (data) {
          var referenceExpectedWeight = this.referenceWeight
          this.scaleScale = (data.raw - this.scaleOffset) / referenceExpectedWeight
          this.stopProgressAnimation()
        })
        .catch((err) => {
          console.log("error completing request", err)
          this.stopProgressAnimation()
        })
    },
    recalibrate() {
      this.currentStep = 1
      this.scaleOffset = null
      this.scaleScale = null
      this.currentWeight = null
      this.referenceWeight = null
    },
    requestTare() {
      this.startProgressAnimation()
      fetch("/raw-weight-idle?board=" + this.$cookies.get("hw-module"))
        .then((response) => {
          return response.json()
        })
        .then(function (data) {
          this.scaleOffset = data.raw
          this.currentWeight = 0

          this.stopProgressAnimation()
        })
        .catch((err) => {
          console.log("error setting tare", err)
          this.stopProgressAnimation()
        })
    },
    requestMeasure() {
      this.startProgressAnimation()
      fetch("/raw-weight-idle?board=" + this.$cookies.get("hw-module"))
        .then((response) => {
          return response.json()
        })
        .then(function (data) {
          const offset = parseFloat(this.scaleOffset)
          const scale = parseFloat(this.scaleScale)
          if (scale !== 0) {
            let weight = (data.raw - offset) / scale
            this.currentWeight = Math.round(weight)
          }

          this.stopProgressAnimation()
        })
        .catch((err) => {
          console.log("error completing request", err)
          this.stopProgressAnimation()
        })
    },
    goToPreviousStep() {
      this.currentStep--
    },
    saveCalibration() {
      this.closeWizard()
      this.storeData()
    }
  },
  computed: {
    // Add your computed properties here
  }
}
</script>

<style scoped>
.network {
  /* Add your component styles here */
}
</style>
