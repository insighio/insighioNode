<template>
  <div class="form-group">
    <br />
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
      <SDivider label="Generic Configuration" />
      <SRadioGroup
        label="Protocol"
        v-model:value="protocol"
        @update:value="protocol = $event"
        :valueOptions="protocol_options"
        :colsLabel="3"
        :colsInput="9"
      />
      <div class="text-normal">
        SSIDs in range:
        <button class="btn btn-primary" type="button" @click="updateWifiList()">Refresh</button>
      </div>
      <table class="table table-striped table-hover">
        <thead>
          <tr>
            <th>SSID</th>
            <th>rssi</th>
            <th>Quality</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="network in wifiAvailableNets" :key="network.ssid" @click="ssidSelected(network)">
            <td class="pointer">{{ network.ssid }}</td>
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
import SRadioGroup from "@/components/SRadioGroup.vue"

export default {
  name: "NetworkWifi",
  mixins: [CommonTools],
  components: { SDivider, SInput, SRadioGroup },
  data() {
    return {
      // Add your component data here
      wifi_ssid: undefined,
      wifi_pass: undefined,
      protocol: undefined,
      wifiAvailableNets: [],
      localLoading: false,
      protocol_options: [
        {
          label: "MQTT",
          value: "mqtt"
        },
        {
          label: "CoAP",
          value: "coap"
        }
      ]
    }
  },
  mounted() {
    this.initializeValues()
  },
  methods: {
    // Add your component methods here
    initializeValues() {
      this.protocol = this.getValueWithDefaults(this.$cookies.get("protocol"), "mqtt")
      this.wifi_ssid = this.$cookies.get("wifi-ssid")
      this.wifi_pass = this.$cookies.get("wifi-pass")
    },
    updateWifiList() {
      if (this.localLoading) return

      this.localLoading = true
      fetchInternal("/update_wifi_list")
        .then((data) => {
          this.wifiAvailableNets = data.wifiAvailableNets
        })
        .catch((err) => console.error("Error fetching WiFi list:", err))
        .finally(() => {
          this.localLoading = false
        })
    },
    storeData() {
      //wifi
      this.$cookies.set("network", "wifi")
      this.$cookies.set("wifi-ssid", this.wifi_ssid.trim())
      this.$cookies.set("wifi-pass", this.wifi_pass ? this.wifi_pass.trim() : "")
      this.$cookies.set("protocol", this.protocol)
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
