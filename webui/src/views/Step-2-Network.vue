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
            <button class="btn" :disabled="disableButtons" @click="operationSelected('WiFi')">WiFi</button>
            <button class="btn" :disabled="disableButtons" @click="operationSelected('Cellular')">Cellular</button>
            <button class="btn" :disabled="disableButtons" @click="operationSelected('LoRa')">LoRa</button>
            <button class="btn" :disabled="disableButtons" @click="operationSelected('Satellite')">Satellite</button>
          </div>
          <div v-if="evaluatedNetwork === 'wifi'">
            <NetworkWifi @goNext="requestGoNext()" @goBack="activeNetwork = undefined" />
          </div>
          <div v-else-if="evaluatedNetwork === 'cellular'">
            <NetworkCellular @goNext="requestGoNext()" @goBack="activeNetwork = undefined" />
          </div>
          <div v-else-if="evaluatedNetwork === 'lora'">
            <NetworkLoRa @goNext="requestGoNext()" @goBack="activeNetwork = undefined" />
          </div>
          <div v-else-if="evaluatedNetwork === 'satellite'">
            <NetworkSatAstro @goNext="requestGoNext()" @goBack="activeNetwork = undefined" />
          </div>
        </div>
      </div>
      <br />
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

import CommonTools from "@/components/mixins/CommonTools.vue"

export default {
  name: "Step2Network",
  mixins: [CommonTools],
  components: {
    NetworkWifi,
    NetworkCellular,
    NetworkLoRa,
    NetworkSatAstro
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
      settingsAcquired: false
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
    }
  }
}
</script>
