<template>
  <div class="panel-body">
    <br />
    <div class="text-center">Configuration details for: <span class="text-bold">Cellular</span></div>
    <br />
    <div class="container grid-lg">
      <div class="columns flex-centered">
        <div class="column col-xl-7 col-md-10 col-sm-12">
          <div class="form-group">
            <div class="columns">
              <div class="col-12">
                <div class="divider text-center" data-content="Connection Configuration"></div>
              </div>
              <br />
              <br />
              <div class="col-3 col-sm-12">
                <label class="form-label" for="input-example-cellular">APN</label>
              </div>
              <div class="col-9 col-sm-12">
                <input class="form-input constr-field" type="text" v-model="cell_apn" />
              </div>
              <br />
              <br />
              <div class="col-3 col-sm-12">
                <label class="form-label" for="measurements">Technology</label>
              </div>
              <div class="col-9 col-sm-12">
                <select class="form-select" v-model="cell_tech">
                  <option v-for="tech in cell_tech_options" :key="tech" :value="tech">{{ tech }}</option>
                </select>
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
              <div class="col-3 col-sm-12">
                <label class="form-label" for="input-example-cellular">IP version</label>
              </div>
              <div class="col-9 col-sm-12">
                <label class="form-radio">
                  <input type="radio" value="IP" v-model="ipversion" />
                  <i class="form-icon"></i> IPv4
                </label>
                <label class="form-radio">
                  <input type="radio" value="IPV6" v-model="ipversion" />
                  <i class="form-icon"></i> IPv6
                </label>
                <label class="form-radio">
                  <input type="radio" value="IPV4V6" v-model="ipversion" />
                  <i class="form-icon"></i> IPv4/v6
                </label>
              </div>
              <br />
              <br />
            </div>
          </div>
          <div class="column col-12">
            <button
              class="btn btn-primary float-right"
              @click="validateMyForm()"
              id="save-button"
              style="margin-left: 30px"
            >
              Save
            </button>
            <button class="btn btn-primary float-right" type="button" id="back-button" @click="requestGoBack">
              Back
            </button>
          </div>
          <br />
          <br />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"

export default {
  name: "NetworkCellular",
  mixins: [CommonTools],
  data() {
    return {
      // Add your component data here
      protocol: "mqtt",
      ipversion: "IP",
      cell_tech: "NBIoT",
      cell_apn: "iot.1nce.net",
      cell_band: 20,
      cell_tech_options: ["GSM", "NBIoT", "LTE-M", "auto"]
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
