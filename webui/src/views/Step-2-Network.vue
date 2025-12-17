<template>
  <div class="panel-body">
    <br />
    <div class="text-center">Select network technology to be used:</div>
    <br />
    <div v-show="localLoading" class="loading loading-lg"></div>
    <br />
    <div class="container grid-lg">
      <div class="columns flex-centered">
        <div class="column col-xl-7 col-md-10 col-sm-12">
          <div class="btn-group btn-group-block img-center">
            <button class="btn" :disabled="disableButtons || noNetworkSelected" @click="operationSelected('WiFi')">
              WiFi
            </button>
            <button class="btn" :disabled="disableButtons || noNetworkSelected" @click="operationSelected('Cellular')">
              Cellular
            </button>
            <button class="btn" :disabled="disableButtons || noNetworkSelected" @click="operationSelected('LoRa')">
              LoRa
            </button>
            <button class="btn" :disabled="disableButtons || noNetworkSelected" @click="operationSelected('Satellite')">
              Satellite
            </button>
          </div>
          <br />
          <!-- check box with the option "No Network"-->
          <label class="form-checkbox">
            <input
              type="checkbox"
              v-model="noNetworkSelected"
              :disabled="disableButtons"
              @click="noNetworkSelectedChanged"
            />
            <i class="form-icon"></i>
            No Network
          </label>
        </div>
        <div v-if="evaluatedNetwork === 'wifi'">
          <NetworkWifi ref="wifiComponent" />
        </div>
        <div v-else-if="evaluatedNetwork === 'cellular'">
          <NetworkCellular ref="cellularComponent" />
        </div>
        <div v-else-if="evaluatedNetwork === 'lora'">
          <NetworkLoRa ref="loraComponent" />
        </div>
        <div v-else-if="evaluatedNetwork === 'satellite'">
          <NetworkSatAstro ref="satelliteComponent" />
        </div>
      </div>
      <br />
      <div class="columns">
        <WebuiFooter :showBackButton="false" @savePressed="handleSave" @backPressed="handleBack" />
      </div>
    </div>
  </div>
</template>

<script>
import "@/assets/css/spectre.min.css"
import "@/assets/css/style.css"
import { fetchInternal } from "@/js/utils.js"

import NetworkWifi from "@/views/networkConfigs/Step-2-Network-Wifi.vue"
import NetworkCellular from "@/views/networkConfigs/Step-2-Network-Cellular.vue"
import NetworkLoRa from "@/views/networkConfigs/Step-2-Network-Lora.vue"
import NetworkSatAstro from "@/views/networkConfigs/Step-2-Network-Sat-Astro.vue"
import WebuiFooter from "@/components/WebuiFooter.vue"

import CommonTools from "@/components/mixins/CommonTools.vue"

export default {
  name: "Step2Network",
  mixins: [CommonTools],
  components: {
    NetworkWifi,
    NetworkCellular,
    NetworkLoRa,
    NetworkSatAstro,
    WebuiFooter
  },
  computed: {
    evaluatedNetwork() {
      if (this.activeNetwork) return this.activeNetwork.toLowerCase()
      else return undefined
    }
  },
  data() {
    return {
      activeNetwork: undefined,
      localLoading: false,
      settingsAcquired: false,
      noNetworkSelected: false
    }
  },
  mounted() {
    this.initializeValues()
  },
  methods: {
    initializeValues() {
      if (this.settingsAcquired || this.localLoading) return

      this.localLoading = true
      this.disableButtonsLocal()

      console.log("in here.....")

      fetchInternal("/settings")
        .then((data) => {
          Object.keys(data).forEach((key) => {
            this.$cookies.set(key.replaceAll("_", "-"), data[key])
          })
          this.enableButtonsLocal()
          this.localLoading = false
          this.settingsAcquired = true

          this.activeNetwork = this.$cookies.get("network")

          // Highlight the corresponding button based on activeNetwork value
          this.$nextTick(() => {
            if (this.activeNetwork) {
              const buttons = this.$el.querySelectorAll(".btn-group .btn")
              buttons.forEach((btn) => btn.classList.remove("btn-primary"))

              const networkMap = {
                wifi: "WiFi",
                cellular: "Cellular",
                lora: "LoRa",
                satellite: "Satellite"
              }

              const targetText = networkMap[this.activeNetwork.toLowerCase()]
              if (targetText) {
                const targetButton = Array.from(buttons).find((btn) => btn.textContent.trim() === targetText)
                if (targetButton) {
                  targetButton.classList.add("btn-primary")
                }
              }
            }
          })
        })
        .catch((err) => {
          console.log("error completing request", err)
          this.enableButtonsLocal()
          this.localLoading = false
        })
    },

    operationSelected(operationName) {
      this.activeNetwork = operationName
    },

    noNetworkSelectedChanged() {
      setTimeout(() => {
        console.log("noNetworkSelected changed to:", this.noNetworkSelected)
        if (this.noNetworkSelected) {
          this.activeNetwork = undefined
        }
      }, 250)
    },

    handleSave() {
      // Disable buttons to prevent multiple submissions
      //this.disableButtonsLocal()

      // call all child components to clear their cookies
      this.$refs["wifiComponent"]?.clearCookies()
      this.$refs["cellularComponent"]?.clearCookies()
      this.$refs["loraComponent"]?.clearCookies()
      this.$refs["satelliteComponent"]?.clearCookies()

      // Call the active child component's validateMyForm method
      if (this.noNetworkSelected) {
        this.requestGoNext()
      } else {
        const componentMap = {
          wifi: "wifiComponent",
          cellular: "cellularComponent",
          lora: "loraComponent",
          satellite: "satelliteComponent"
        }

        const refName = componentMap[this.evaluatedNetwork]
        if (refName && this.$refs[refName]) {
          this.$refs[refName].validateMyForm()
        }
      }
    },

    handleBack() {
      this.activeNetwork = undefined
    }
  }
}
</script>
