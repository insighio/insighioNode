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

      <WebuiFooter @savePressed="validateMyForm" @backPressed="requestGoBack" />
    </div>
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"
import SInput from "@/components/SInput.vue"
import SSelect from "@/components/SSelect.vue"
import SRadioGroup from "@/components/SRadioGroup.vue"
import SDivider from "@/components/SDivider.vue"
import WebuiFooter from "@/components/WebuiFooter.vue"

export default {
  name: "NetworkCellular",
  mixins: [CommonTools],
  components: { SInput, SSelect, SRadioGroup, SDivider, WebuiFooter },
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
      ]
    }
  },
  methods: {
    initializeValues() {
      this.protocol = this.getValueWithDefaults(this.$cookies.get("protocol"), "mqtt")
      this.ipversion = this.getValueWithDefaults(this.$cookies.get("ipversion"), "IP")

      this.cell_tech = this.getValueWithDefaults(this.$cookies.get("cell-tech"), "NBIoT")
      this.cell_apn = this.getValueWithDefaults(this.$cookies.get("cell-apn"), "iot.1nce.net")
      this.cell_band = this.getValueWithDefaults(this.$cookies.get("cell-band"), 20)
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

      this.requestGoNext()
    },

    validateMyForm() {
      if (this.cell_apn.trim() === "") {
        window.alert("Please enter an APN")
        return false
      }

      this.storeData()
      return true
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
