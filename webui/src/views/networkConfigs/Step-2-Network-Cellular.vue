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

      <div class="column col-12"><br /></div>
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
                      <span class="label" :class="modemInfo.status === 'connected' ? 'label-success' : 'label-warning'">
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
                    <td>{{ modemInfo.rssi }} dBm</td>
                  </tr>
                  <tr>
                    <td style="font-weight: 500">RSRP</td>
                    <td>{{ modemInfo.rsrp }} dBm</td>
                  </tr>
                  <tr>
                    <td style="font-weight: 500">RSRQ</td>
                    <td>{{ modemInfo.rsrq }} dB</td>
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
                    <td>{{ modemInfo.activation_duration }} s</td>
                  </tr>
                  <tr>
                    <td style="font-weight: 500">Attachment</td>
                    <td>{{ modemInfo.attachment_duration }} s</td>
                  </tr>
                  <tr>
                    <td style="font-weight: 500">Connection</td>
                    <td>{{ modemInfo.connection_duration }} s</td>
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
    },
    async updateModemInfo() {
      // Implement modem info update if needed
      if (this.localLoading) return

      this.localLoading = true
      const bodyLocal = JSON.stringify({ IP: this.ipversion, technology: this.cell_tech, apn: this.cell_apn })
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
    get_signal_quality(rssi, rsrp, rsrq, technology) {
      // Implement signal quality calculation if needed
      if (technology === "GSM") {
        if (rssi >= -70) return { str: "Excellent", color: "green" }
        else if (rssi >= -85) return { str: "Good", color: "#6ACE61" }
        else if (rssi >= -100) return { str: "Fair", color: "#F7BA30" }
        else return { str: "Bad", color: "#E01B24" }
      } else if (technology === "NBIoT") {
        if (rsrp >= -80 && rsrq >= -10) return { str: "Excellent", color: "green" }
        else if (rsrp >= -90 && rsrq >= -15) return { str: "Good", color: "#6ACE61" }
        else if (rsrp >= -100 && rsrq < -15) return { str: "Fair", color: "#F7BA30" }
        else return { str: "Bad", color: "#E01B24" }
      } else if (technology === "LTE-M") {
        if (rsrp >= -75) return { str: "Excellent", color: "green" }
        else if (rsrp >= -85) return { str: "Good", color: "#6ACE61" }
        else if (rsrp >= -98) return { str: "Fair", color: "#F7BA30" }
        else return { str: "Bad", color: "#E01B24" }
      }
      return "Unknown"
    },
    clearCookies() {
      this.$cookies.remove("network")
      this.$cookies.remove("cell-apn")
      this.$cookies.remove("cell-band")
      this.$cookies.remove("protocol")
      this.$cookies.remove("cell-tech")
      this.$cookies.remove("ipversion")
    },
    storeData() {
      this.clearCookies()
      this.$cookies.set("network", "cellular")
      this.$cookies.set("cell-tech", this.cell_tech)
      this.$cookies.set("cell-apn", this.cell_apn.trim())
      this.$cookies.set("cell-band", this.cell_band)
      this.$cookies.set("protocol", this.protocol)
      this.$cookies.set("ipversion", this.ipversion)
    },

    validateMyForm() {
      if (this.cell_apn.trim() === "") {
        window.alert("Please enter an APN")
        return false
      }

      this.storeData()
      this.requestGoNext()
      return true
    }
  }
}
</script>
