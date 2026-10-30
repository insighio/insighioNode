<template>
  <div class="form-group ui-pt-1">
    <div class="columns">
      <SDivider label="Connection Configuration" />
      <SInput label="SSID" v-model:value="wifi_ssid" @update:value="wifi_ssid = $event" :colsLabel="3" :colsInput="9" />
      <SInput
        label="Password"
        v-model:value="wifi_pass"
        @update:value="wifi_pass = $event"
        :colsLabel="3"
        :colsInput="9"
        ref="passwordInput"
      />
      <div class="text-normal">
        SSIDs in range:
        <button class="btn btn-primary" type="button" :disabled="localLoading" @click="updateWifiList()">
          {{ localLoading ? "Scanning..." : "Refresh" }}
        </button>
      </div>
      <p v-if="scanError" class="toast toast-error" role="alert">{{ scanError }}</p>
      <table class="table table-striped table-hover wifi-networks">
        <colgroup>
          <col style="width: 50%" />
          <col style="width: 25%" />
          <col style="width: 25%" />
        </colgroup>
        <thead>
          <tr>
            <th>SSID</th>
            <th>RSSI (dBm)</th>
            <th>Quality</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="network in wifiAvailableNets" :key="network.ssid" @click="ssidSelected(network)">
            <td>
              <button class="btn btn-link" type="button" @click.stop="ssidSelected(network)">{{ network.ssid }}</button>
            </td>
            <td class="pointer">{{ network.rssi }}</td>
            <td class="pointer">
              <span
                :style="
                  'color:' +
                  (network.rssi >= -67 ? 'green' : network.rssi < -67 && network.rssi >= -89 ? '#E2B200' : '#A2021A')
                "
                >{{
                  network.rssi >= -50
                    ? "very good"
                    : network.rssi < -50 && network.rssi >= -67
                      ? "good"
                      : network.rssi < -67 && network.rssi >= -89
                        ? "fair"
                        : "bad"
                }}</span
              >
            </td>
          </tr>
        </tbody>
      </table>
      <div v-show="localLoading" class="loading loading-lg"></div>
    </div>
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"
import { fetchInternal } from "@/js/utils.js"

import SDivider from "@/components/SDivider.vue"
import SInput from "@/components/SInput.vue"

export default {
  name: "NetworkWifi",
  mixins: [CommonTools],
  components: { SDivider, SInput },
  data() {
    return {
      // Add your component data here
      wifi_ssid: undefined,
      wifi_pass: undefined,
      wifiAvailableNets: [],
      localLoading: false,
      scanError: ""
    }
  },
  mounted() {
    this.initializeValues()
  },
  methods: {
    // Add your component methods here
    initializeValues() {
      this.wifi_ssid = this.$storage.get("wifi-ssid")
      this.wifi_pass = this.$storage.get("wifi-pass")
    },
    updateWifiList() {
      if (this.localLoading) return

      this.localLoading = true
      this.scanError = ""
      fetchInternal("/update_wifi_list")
        .then((data) => {
          this.wifiAvailableNets = data.wifiAvailableNets
          if (!this.wifiAvailableNets.length)
            this.scanError = "No networks found. Try scanning again or enter an SSID above."
        })
        .catch((err) => {
          console.error("Error fetching WiFi list:", err)
          this.scanError = "Could not scan for networks. Check your device connection and try again."
        })
        .finally(() => {
          this.localLoading = false
        })
    },
    storeData() {
      //wifi
      this.$storage.set("network", "wifi")
      this.$storage.set("wifi-ssid", this.wifi_ssid.trim())
      this.$storage.set("wifi-pass", this.wifi_pass ? this.wifi_pass.trim() : "")
    },
    ssidSelected(network) {
      this.wifi_ssid = network.ssid
      this.$nextTick(() => {
        this.$refs.passwordInput.focusInput()
      })
    },
    validateMyForm() {
      if (!this.wifi_ssid) {
        alert("please fill SSID info")
        return false
      }

      this.storeData()
      return true
    }
  }
}
</script>

<style scoped>
.wifi-networks .btn-link {
  padding: 0;
  text-align: left;
  width: 100%;
}
</style>
