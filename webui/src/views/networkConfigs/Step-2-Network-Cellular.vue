<template>
  <div class="form-group">
    <br />
    <div class="columns">
      <SDivider label="Connection Configuration" />

      <SInput label="APN" v-model:value="cell_apn" @update:value="cell_apn = $event" :colsLabel="3" :colsInput="9" />

      <SSelect
        label="Technology"
        v-model:value="cell_tech"
        @update:value="cell_tech = $event"
        :valueOptions="cell_tech_options"
        :colsLabel="3"
        :colsInput="9"
      />

      <SDivider label="Optional Configuration" />
      <label class="form-checkbox">
        <input type="checkbox" v-model="cell_mcc_mnc_enabled" :disabled="disableButtons" />
        <i class="form-icon"></i>
        Enable Operator Preference
      </label>
      <div class="accordion col-12">
        <SInput
          v-if="cell_mcc_mnc_enabled"
          label="MMC/MNC"
          v-model:value="cell_mcc_mnc"
          inputType="number"
          @update:value="cell_mcc_mnc = $event"
          :colsLabel="3"
          :colsInput="9"
        />

        <div class="column col-12"><br /></div>
        <!-- Network Discovery Section -->
        <div class="column col-12" v-if="cell_mcc_mnc_enabled">
          <button class="btn btn-primary" :disabled="discoverLoading" type="button" @click="discoverNetworks()">
            Discover Networks
          </button>
          <div
            v-show="discoverLoading"
            style="margin-left: 5px; display: inline-block; width: 200px; vertical-align: middle"
          >
            <progress class="progress" :value="discoverProgress" max="200"></progress>
            <!--span style="margin-left: 5px; font-size: 0.9rem">{{ discoverProgress }} / 200s</span-->
          </div>
        </div>
        <div class="column col-12"><br /></div>

        <!-- Networks Table -->
        <div class="column col-12" v-if="discoveredNetworks.length > 0">
          <div class="card" style="padding: 0.8rem; margin-top: 1rem">
            <div class="card-header">
              <div class="card-title h5">Available Networks</div>
            </div>
            <div class="card-body" style="padding: 0.4rem 0">
              <table class="table table-striped table-hover">
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>Operator</th>
                    <th>MCC/MNC</th>
                    <th>Technology</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="network in discoveredNetworks" :key="network.mcc_mnc">
                    <td>
                      <span
                        class="label"
                        :class="{
                          'label-success': network.status === 2,
                          'label-primary': network.status === 1,
                          'label-error': network.status === 3,
                          'label-default': network.status === 0
                        }"
                      >
                        {{ getNetworkStatusLabel(network.status) }}
                      </span>
                    </td>
                    <td>{{ network.long_name }}</td>
                    <td>{{ network.mcc_mnc }}</td>
                    <td>{{ getNetworkTechnologyArrayLabel(network.technology_ids) }}</td>
                    <td>
                      <button
                        class="btn btn-sm btn-primary"
                        @click="selectNetwork(network.mcc_mnc)"
                        :disabled="network.status === 3"
                      >
                        Select
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <SDivider label="Generic Configuration" />

      <SRadioGroup
        label="Protocol"
        v-model:value="protocol"
        @update:value="protocol = $event"
        :valueOptions="protocol_options"
        :colsLabel="3"
        :colsInput="9"
      />

      <SRadioGroup
        label="IP version"
        v-model:value="ipversion"
        @update:value="ipversion = $event"
        :valueOptions="ipversion_options"
        :colsLabel="3"
        :colsInput="9"
      />

      <div class="column col-12 text-normal">
        Modem Connection:
        <button class="btn btn-primary" :disabled="localLoading" type="button" @click="updateModemInfo()">Test</button>
        <div v-show="localLoading" class="loading loading-lg" style="margin-left: 5px"></div>
      </div>
      <div class="column col-12"><br /></div>

      <div class="column col-12">
        <div v-if="modemInfo.updated" class="card" style="padding: 0.8rem">
          <div class="card-header">
            <div class="card-title h5">Modem Information</div>
          </div>
          <div class="card-body" style="padding: 0.4rem 0">
            <!-- Connection Status Section -->
            <div style="margin-bottom: 1rem">
              <div class="text-bold text-primary" style="margin-bottom: 0.5rem">Connection Status</div>
              <table class="table" style="margin-bottom: 0">
                <tbody>
                  <tr>
                    <td style="width: 40%; font-weight: 500">Status</td>
                    <td>
                      <span
                        class="label"
                        :class="
                          modemInfo.status === 'connected'
                            ? 'label-success'
                            : modemInfo.status === 'disconnected'
                              ? 'label-error'
                              : 'label-warning'
                        "
                      >
                        {{ modemInfo.status }}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td style="font-weight: 500">Technology</td>
                    <td>
                      <strong>{{ modemInfo.technology }}</strong>
                    </td>
                  </tr>
                  <tr>
                    <td style="font-weight: 500">MCC / MNC</td>
                    <td>{{ modemInfo.mcc }} / {{ modemInfo.mnc }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Signal Quality Section -->
            <div style="margin-bottom: 1rem">
              <div class="text-bold text-primary" style="margin-bottom: 0.5rem">Signal Quality</div>
              <table class="table" style="margin-bottom: 0">
                <tbody>
                  <tr>
                    <td style="width: 40%; font-weight: 500">Quality</td>
                    <td>
                      <span
                        class="label"
                        :style="'background-color:' + modemInfo.signal_quality.color + '; color: white;'"
                      >
                        {{ modemInfo.signal_quality.str }}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td style="font-weight: 500">RSSI</td>
                    <td>
                      <div>{{ modemInfo.rssi }} dBm</div>
                      <div class="bar" style="height: 8px; margin-top: 4px">
                        <div
                          class="bar-item"
                          :style="{
                            width: getSignalPercentage(modemInfo.rssi, -120, -50) + '%',
                            backgroundColor: get_rssi_quality(modemInfo.rssi).color
                          }"
                        ></div>
                      </div>
                    </td>
                  </tr>
                  <tr>
                    <td style="font-weight: 500">RSRP</td>
                    <td>
                      <div v-if="modemInfo.technology !== 'GSM'">
                        <div>{{ modemInfo.rsrp }} dBm</div>
                        <div class="bar" style="height: 8px; margin-top: 4px">
                          <div
                            class="bar-item"
                            :style="{
                              width: getSignalPercentage(modemInfo.rsrp, -120, -5) + '%',
                              backgroundColor: get_rsrp_quality(modemInfo.rsrp).color
                            }"
                          ></div>
                        </div>
                      </div>
                      <div v-else>N/A</div>
                    </td>
                  </tr>
                  <tr>
                    <td style="font-weight: 500">RSRQ</td>
                    <td>
                      <div v-if="modemInfo.technology !== 'GSM'">
                        <div>{{ modemInfo.rsrq }} dB</div>
                        <div class="bar" style="height: 8px; margin-top: 4px">
                          <div
                            class="bar-item"
                            :style="{
                              width: getSignalPercentage(modemInfo.rsrq, -20, 20) + '%',
                              backgroundColor: get_rsrq_quality(modemInfo.rsrq).color
                            }"
                          ></div>
                        </div>
                      </div>
                      <div v-else>N/A</div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Connection Timing Section -->
            <div>
              <div class="text-bold text-primary" style="margin-bottom: 0.5rem">Connection Timing</div>
              <table class="table" style="margin-bottom: 0">
                <tbody>
                  <tr>
                    <td style="width: 40%; font-weight: 500">Activation</td>
                    <td>{{ modemInfo.activation_duration }} ms</td>
                  </tr>
                  <tr>
                    <td style="font-weight: 500">Attachment</td>
                    <td>{{ modemInfo.attachment_duration }} ms</td>
                  </tr>
                  <tr>
                    <td style="font-weight: 500">Connection</td>
                    <td>{{ modemInfo.connection_duration }} ms</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"
import SInput from "@/components/SInput.vue"
import SSelect from "@/components/SSelect.vue"
import SRadioGroup from "@/components/SRadioGroup.vue"
import SDivider from "@/components/SDivider.vue"

export default {
  name: "NetworkCellular",
  mixins: [CommonTools],
  components: { SInput, SSelect, SRadioGroup, SDivider },
  data() {
    return {
      // Add your component data here
      protocol: "mqtt",
      ipversion: "IP",
      cell_tech: "NBIoT",
      cell_apn: "iot.1nce.net",
      cell_band: 20,
      cell_mcc_mnc: "20201",
      cell_mcc_mnc_enabled: false,
      cell_tech_options: [
        { value: "GSM", label: "GSM" },
        { value: "NBIoT", label: "NBIoT" },
        { value: "LTE-M", label: "LTE-M" },
        { value: "auto", label: "auto" }
      ],
      protocol_options: [
        {
          label: "MQTT",
          value: "mqtt"
        },
        {
          label: "CoAP",
          value: "coap"
        }
      ],
      ipversion_options: [
        {
          label: "IPv4",
          value: "IP"
        },
        {
          label: "IPv6",
          value: "IPV6"
        },
        {
          label: "IPv4/v6",
          value: "IPV4V6"
        }
      ],
      localLoading: false,
      discoverLoading: false,
      discoverProgress: 0,
      discoverProgressInterval: null,
      discoveredNetworks: [],
      modemInfo: {
        updated: false,
        status: "",
        activation_duration: "",
        attachment_duration: "",
        connection_duration: "",
        technology: "",
        signal_quality: {},
        mcc: "",
        mnc: "",
        rssi: "",
        rsrp: "",
        rsrq: ""
      }
    }
  },
  mounted() {
    this.initializeValues()
  },
  methods: {
    initializeValues() {
      this.protocol = this.getValueWithDefaults(this.$cookies.get("protocol"), "mqtt")
      this.ipversion = this.getValueWithDefaults(this.$cookies.get("ipversion"), "IP")

      this.cell_tech = this.getValueWithDefaults(this.$cookies.get("cell-tech"), "NBIoT")
      this.cell_apn = this.getValueWithDefaults(this.$cookies.get("cell-apn"), "iot.1nce.net")
      this.cell_band = this.getValueWithDefaults(this.$cookies.get("cell-band"), 20)
      this.cell_mcc_mnc = this.getValueWithDefaults(this.$cookies.get("cell-mcc-mnc"), "20201")
      this.cell_mcc_mnc_enabled = this.getValueWithDefaults(this.$cookies.get("cell-mcc-mnc"), null) !== null
    },
    async updateModemInfo() {
      // Implement modem info update if needed
      if (this.localLoading) return

      this.localLoading = true
      const bodyLocal = JSON.stringify({
        IP: this.ipversion,
        technology: this.cell_tech,
        apn: this.cell_apn,
        mcc_mnc: this.cell_mcc_mnc_enabled ? this.cell_mcc_mnc : null
      })
      try {
        const rawResponse = await fetch("http://192.168.4.1/api/modem_info", {
          method: "POST",
          headers: {
            Accept: "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Content-Length": bodyLocal.length.toString()
          },
          body: bodyLocal
        })

        const data = await rawResponse.json()
        this.modemInfo.status = data.status
        this.modemInfo.activation_duration = data.activation_duration
        this.modemInfo.attachment_duration = data.attachment_duration
        this.modemInfo.connection_duration = data.connection_duration
        this.modemInfo.rssi = data.rssi
        this.modemInfo.rsrp = data.rsrp
        this.modemInfo.rsrq = data.rsrq
        this.modemInfo.signal_quality = this.get_signal_quality(data.rssi, data.rsrp, data.rsrq, data.technology)
        this.modemInfo.technology = data.technology
        this.modemInfo.mcc = data.mcc
        this.modemInfo.mnc = data.mnc
        this.modemInfo.updated = true
        this.localLoading = false
      } catch (error) {
        console.log("error getting modem error: ", error)
        this.localLoading = false
        alert("Error updating modem info. Please check your connection and try again.")
      }
    },
    getSignalPercentage(value, min, max) {
      const percentage = ((value - min) / (max - min)) * 100
      return Math.max(0, Math.min(100, percentage))
    },
    get_signal_quality(rssi, rsrp, rsrq, technology) {
      // Implement signal quality calculation if needed
      if (technology === "GSM") {
        return this.get_rssi_quality(rssi)
      } else if (technology === "NBIoT") {
        return this.get_rsrp_quality(rsrp)
      } else if (technology === "LTE-M") {
        return this.get_rsrq_quality(rsrq)
      }
      return "Unknown"
    },
    get_rssi_quality(rssi) {
      if (rssi >= -70) return { str: "Excellent", color: "green" }
      else if (rssi >= -85) return { str: "Good", color: "#6ACE61" }
      else if (rssi >= -100) return { str: "Fair", color: "#F7BA30" }
      else return { str: "Bad", color: "#E01B24" }
    },
    get_rsrp_quality(rsrp) {
      if (rsrp >= -80) return { str: "Excellent", color: "green" }
      else if (rsrp >= -90) return { str: "Good", color: "#6ACE61" }
      else if (rsrp >= -100) return { str: "Fair", color: "#F7BA30" }
      else return { str: "Bad", color: "#E01B24" }
    },
    get_rsrq_quality(rsrq) {
      if (rsrq >= -10) return { str: "Excellent", color: "green" }
      else if (rsrq >= -15) return { str: "Good", color: "#6ACE61" }
      else if (rsrq >= -20) return { str: "Fair", color: "#F7BA30" }
      else return { str: "Bad", color: "#E01B24" }
    },
    async discoverNetworks() {
      if (this.discoverLoading) return

      this.discoverLoading = true
      this.discoveredNetworks = []
      this.discoverProgress = 0

      // Start progress bar increment
      this.discoverProgressInterval = setInterval(() => {
        if (this.discoverProgress < 200 && this.discoverLoading) {
          this.discoverProgress++
        }
      }, 1000)

      try {
        const rawResponse = await fetch("http://192.168.4.1/api/modem_nearby_networks", {
          method: "GET",
          headers: {
            Accept: "application/json, text/plain, */*"
          }
        })

        const data = await rawResponse.json()
        if (data.networks && Array.isArray(data.networks)) {
          let tmpList = data.networks.sort((a, b) => a.mcc_mnc.localeCompare(b.mcc_mnc))
          let networkMap = {}

          tmpList.forEach((network) => {
            const isForbidden = network.status === 3
            // Create separate keys for forbidden and non-forbidden networks
            const key = network.mcc_mnc + (isForbidden ? "_forbidden" : "")

            if (!networkMap[key]) {
              networkMap[key] = {
                mcc_mnc: network.mcc_mnc,
                long_name: network.long_name,
                technology_ids: [network.technology_id],
                status: network.status
              }
            } else {
              // Add technology if not already present
              if (!networkMap[key].technology_ids.includes(network.technology_id)) {
                networkMap[key].technology_ids.push(network.technology_id)
              }
              // Update status to the highest priority (2=current > 1=available > 0=unknown)
              // Don't update status for forbidden networks
              if (!isForbidden && network.status > networkMap[key].status) {
                networkMap[key].status = network.status
              }
            }
          })

          // Convert to array and sort by status (current first, then available, then forbidden)
          this.discoveredNetworks = Object.values(networkMap).sort((a, b) => b.status - a.status)
        } else {
          alert("No networks found")
        }
      } catch (error) {
        console.log("error discovering networks: ", error)
        alert("Error discovering networks. Please check your connection and try again.")
      } finally {
        this.discoverLoading = false
        if (this.discoverProgressInterval) {
          clearInterval(this.discoverProgressInterval)
          this.discoverProgressInterval = null
        }
      }
    },
    getNetworkStatusLabel(status) {
      // status values: 0: unknown, 1: available, 2: current, 3: forbidden
      const statusLabels = {
        0: "Unknown",
        1: "Available",
        2: "Current",
        3: "Forbidden"
      }
      return statusLabels[status] || "Unknown"
    },
    getNetworkTechnologyLabel(technology_id) {
      const techLabels = {
        0: "GSM",
        9: "NBIoT",
        8: "LTE-M"
      }
      return techLabels[technology_id] || technology_id
    },
    getNetworkTechnologyArrayLabel(technologyArray) {
      if (!Array.isArray(technologyArray)) return ""
      return technologyArray
        .sort((a, b) => a - b) // Sort technology IDs for consistent display
        .map((tech) => this.getNetworkTechnologyLabel(tech))
        .join(", ")
    },
    selectNetwork(mccMnc) {
      this.cell_mcc_mnc = mccMnc
    },
    storeData() {
      this.$cookies.set("network", "cellular")
      this.$cookies.set("cell-tech", this.cell_tech)
      this.$cookies.set("cell-apn", this.cell_apn.trim())
      this.$cookies.set("cell-band", this.cell_band)
      this.$cookies.set("protocol", this.protocol)
      this.$cookies.set("ipversion", this.ipversion)
      if (this.cell_mcc_mnc_enabled) {
        this.$cookies.set("cell-mcc-mnc", this.cell_mcc_mnc)
      } else {
        this.$cookies.remove("cell-mcc-mnc")
      }
    },

    validateMyForm() {
      if (this.cell_apn.trim() === "") {
        window.alert("Please enter an APN")
        return false
      }

      this.storeData()
      return true
    }
  }
}
</script>
