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
          <div v-show="activeNetwork === 'WiFi'">
            <NetworkWifi @goNext="requestGoNext()" @goBack="activeNetwork = undefined" />
          </div>
          <div v-show="activeNetwork === 'Cellular'">
            <NetworkCellular @goNext="requestGoNext()" @goBack="activeNetwork = undefined" />
          </div>
          <div v-show="activeNetwork === 'LoRa'">
            <NetworkLoRa @goNext="requestGoNext()" @goBack="activeNetwork = undefined" />
          </div>
          <div v-show="activeNetwork === 'Satellite'">
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
  data() {
    return {
      activeNetwork: undefined,
      localLoading: false,
      settingsAcquired: false
    }
  },
  methods: {
    initializeValues() {
      if (this.settingsAcquired) return

      this.localLoading = true
      this.disableButtonsLocal()

      fetchInternal("/settings")
        .then((data) => {
          Object.keys(data).forEach((key) => {
            this.$cookies.set(key.replaceAll("_", "-"), data[key])
          })
          this.enableButtonsLocal()
          this.localLoading = false
          this.settingsAcquired = true
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
