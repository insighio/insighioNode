<template>
  <div class="form-group">
    <div class="columns">
      <div class="col-12">
        <div class="divider text-center" data-content="Connection Configuration" />
      </div>
      <br />
      <br />
      <div class="col-3 col-sm-12">
        <label class="form-label" for="input-example-1">SSID</label>
      </div>
      <div class="col-9 col-sm-12">
        <input class="form-input constr-field" type="text" v-model="wifi_ssid" />
      </div>
      <br />
      <br />
      <div class="col-3 col-sm-12">
        <label class="form-label" for="input-example-1">Password</label>
      </div>
      <div class="col-9 col-sm-12">
        <input class="form-input constr-field" type="text" v-model="wifi_pass" />
      </div>
      <br />
      <br />
      <div class="col-12">
        <div class="divider text-center" data-content="Generic Configuration"></div>
      </div>
      <br />
      <br />
      <div class="col-3 col-sm-12">
        <label class="form-label" for="input-example-cellular">Protocol</label>
      </div>
      <div class="col-9 col-sm-12">
        <label class="form-radio">
          <input type="radio" name="protocol" value="mqtt" v-model="protocol" />
          <i class="form-icon"></i> MQTT
        </label>
        <label class="form-radio">
          <input type="radio" name="protocol" value="coap" v-model="protocol" />
          <i class="form-icon"></i> CoAP
        </label>
      </div>
      <br />
      <br />
      <div class="column col-12">
        <button class="btn btn-primary float-right" @click="validateMyForm()" style="margin-left: 30px">Save</button>
        <button class="btn btn-primary float-right" type="button" id="back-button" @click="requestGoBack()">
          Back
        </button>
      </div>
      <br />
      <br />
      <div class="text-normal">
        SSIDs in range:
        <button class="btn btn-link tooltip" data-tooltip="Not showing weak networks">
          <i class="icon icon-flag"></i>
        </button>
      </div>
      <table class="table table-striped table-hover">
        <thead>
          <tr>
            <th>SSID</th>
            <th>rssi</th>
            <th>Quality</th>
          </tr>
        </thead>
        <tbody id="ssidList">
          <tr v-for="network in wifiAvailableNets" :key="network.ssid" @click="ssidSelected(network)">
            <td>{{ network.ssid }}</td>
            <td>{{ network.rssi }}</td>
            <td>
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
      <div id="loader" v-show="localLoading" class="loading loading-lg"></div>
    </div>
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"
import { fetchInternal } from "@/js/utils.js"

export default {
  name: "NetworkWifi",
  mixins: [CommonTools],
  data() {
    return {
      // Add your component data here
      wifi_ssid: undefined,
      wifi_pass: undefined,
      protocol: undefined,
      wifiAvailableNets: [],
      localLoading: false
    }
  },
  computed: {
    // Add your computed properties here
  },
  mounted() {
    // Add your mounted logic here
    this.initializeValues()
  },
  methods: {
    // Add your component methods here
    clearCookies() {
      this.$cookies.remove("network")
      this.$cookies.remove("wifi-pass")
      this.$cookies.remove("wifi-ssid")
      this.$cookies.remove("protocol")
    },
    initializeValues() {
      this.protocol = this.$cookies.get("protocol")
      this.wifi_ssid = this.$cookies.get("wifi-ssid")
      this.wifi_pass = this.$cookies.get("wifi-pass")

      this.localLoading = true

      fetchInternal("/update_wifi_list")
        .then((data) => {
          this.wifiAvailableNets = data.wifiAvailableNets
          // detectBoardChange(enableNavigationButtons)
          this.localLoading = false
        })
        .catch((err) => {
          console.log("error completing request", err)
          this.localLoading = false
        })
    },
    storeData() {
      this.clearCookies()

      //wifi
      this.$cookies.set("network", "wifi")
      this.$cookies.set("wifi-ssid", this.wifi_ssid.trim())
      this.$cookies.set("wifi-pass", this.wifi_pass.trim())
      this.$cookies.set("protocol", this.protocol)

      this.requestGoNext()
    },
    ssidSelected(network) {
      this.wifi_ssid = network.ssid
    },
    validateMyForm() {
      if (!this.wifi_ssid) {
        alert("please fill SSID info")
        return
      }

      this.storeData()
    }
  }
}
</script>

<style scoped>
.network {
  /* Add your component styles here */
}
</style>
