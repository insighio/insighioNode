<template>
  <div class="panel-body">
    <br />
    <div class="text-center">Set API keys that were generated during device creation in console.insigh.io.</div>
    <br />
    <div class="container grid-lg">
      <div class="columns flex-centered">
        <div class="column col-xl-7 col-md-10 col-sm-12">
          <div class="form-group">
            <div class="columns">
              <div class="column col-3 col-sm-12">
                <label class="form-label" for="input-id">ID</label>
              </div>
              <div class="column col-9 col-sm-12">
                <input class="form-input constr-field" type="text" v-model="insighio_id" @paste="fillClipboardData" />
              </div>
              <br />
              <br />
              <div class="column col-3 col-sm-12">
                <label class="form-label" for="input-key">KEY</label>
              </div>
              <div class="column col-9 col-sm-12">
                <input class="form-input constr-field" type="text" v-model="insighio_key" @paste="fillClipboardData" />
              </div>
              <br />
              <br />
              <div class="column col-3 col-sm-12">
                <label class="form-label" for="input-channel">Data Channel</label>
              </div>
              <div class="column col-9 col-sm-12">
                <input
                  class="form-input constr-field"
                  type="text"
                  v-model="insighio_channel"
                  @paste="fillClipboardData"
                />
              </div>
              <br />
              <br />
              <div class="column col-3 col-sm-12">
                <label class="form-label" for="input-controlChannel">Control Channel</label>
              </div>
              <div class="column col-9 col-sm-12">
                <input
                  class="form-input constr-field"
                  type="text"
                  v-model="insighio_control_channel"
                  @paste="fillClipboardData"
                />
              </div>
              <br />
              <br />
              <br />
              <SDivider label="Secondary Transmission method" />
              <br />
              <SSwitch
                label="Enable Secondary Measurement Transmission (MQTT)"
                v-model:value="enable_secondary_measurement_transmission"
              />
              <!-- MQTT Configuration Fields - shown when checkbox is enabled -->
              <div class="column col-9 col-sm-12" v-if="enable_secondary_measurement_transmission">
                <div class="columns">
                  <SInput
                    label="MQTT URL"
                    v-model:value="secondary_measurement_transmission_info.mqtt_url"
                    placeholder="mqtt.example.com"
                  />
                  <br />
                  <br />
                  <SInput
                    label="MQTT Port"
                    v-model:value="secondary_measurement_transmission_info.mqtt_port"
                    inputType="number"
                    placeholder="1883"
                  />
                  <br />
                  <br />
                  <SInput label="MQTT Username" v-model:value="secondary_measurement_transmission_info.mqtt_username" />
                  <br />
                  <br />
                  <SInput label="MQTT Password" v-model:value="secondary_measurement_transmission_info.mqtt_password" />
                  <br />
                  <br />

                  <SInput
                    label="MQTT Topic"
                    v-model:value="secondary_measurement_transmission_info.mqtt_topic"
                    placeholder="device/data"
                  />
                  <br />
                  <br />
                  <SSelect
                    label="Package Format"
                    v-model:value="secondary_measurement_transmission_info.format"
                    :valueOptions="package_format_options"
                  />
                  <br />
                  <br />

                  <SSwitch
                    label="Append MAC address to topic"
                    v-model:value="secondary_measurement_transmission_info.append_mac_to_topic"
                  />

                  <br />
                  <br />
                </div>
              </div>
            </div>
            <WebuiFooter @savePressed="validateMyForm" @backPressed="requestGoBack" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"
import WebuiFooter from "@/components/WebuiFooter.vue"
import SSwitch from "@/components/SSwitch.vue"
import SInput from "@/components/SInput.vue"
import SSelect from "@/components/SSelect.vue"
import SDivider from "@/components/SDivider.vue"

export default {
  name: "ApiKeys",
  mixins: [CommonTools],
  components: { WebuiFooter, SSwitch, SInput, SSelect, SDivider },
  data() {
    return {
      // Add your component data here
      insighio_id: "",
      insighio_key: "",
      insighio_channel: "",
      insighio_control_channel: "",
      idRegex: "[0-9a-f]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12}",
      enable_secondary_measurement_transmission: false,
      secondary_measurement_transmission_info: {
        mqtt_url: "",
        mqtt_port: "",
        mqtt_username: "",
        mqtt_password: "",
        mqtt_topic: "",
        append_mac_to_topic: false,
        format: "json_without_units"
      },
      package_format_options: [
        { value: "json_without_units", label: "JSON without units" },
        { value: "json_with_units", label: "JSON with units" },
        { value: "senml", label: "SenML" }
      ]
    }
  },
  methods: {
    initializeValues() {
      this.insighio_id = this.$storage.get("insighio-id")
      this.insighio_key = this.$storage.get("insighio-key")
      this.insighio_channel = this.$storage.get("insighio-channel")
      this.insighio_control_channel = this.$storage.get("insighio-control-channel")

      // Load secondary measurement transmission settings
      this.enable_secondary_measurement_transmission =
        this.strToJSValue(this.$storage.get("enable-secondary-measurement-transmission")) || false
      const savedMqttInfo = this.$storage.get("secondary-measurement-transmission-info")

      if (savedMqttInfo && typeof savedMqttInfo === "string") {
        try {
          this.secondary_measurement_transmission_info = JSON.parse(savedMqttInfo)
        } catch (e) {
          console.log("Error parsing saved MQTT info: ", e, ", from input: ", savedMqttInfo)
        }
      } else this.secondary_measurement_transmission_info = savedMqttInfo
    },
    fillClipboardData(evt) {
      const clipboardData = evt.clipboardData.getData("text")
      if (!clipboardData) {
        return
      }

      setTimeout(() => {
        try {
          var obj = JSON.parse(clipboardData)
          this.insighio_id = obj.id
          this.insighio_key = obj.key
          this.insighio_channel = obj.channel
          this.insighio_control_channel = obj.controlChannel
        } catch (e) {
          console.log("Error parsing clipboard data: ", e)
        }
      }, 100)
      // this.$nextTick(() => {

      // })
    },
    clearCookies() {
      this.$storage.remove("insighio-id")
      this.$storage.remove("insighio-key")
      this.$storage.remove("insighio-channel")
      this.$storage.remove("insighio-control-channel")
      this.$storage.remove("enable-secondary-measurement-transmission")
      this.$storage.remove("secondary-measurement-transmission-info")
    },

    validateMyForm() {
      if (
        !this.validateElemValue(this.insighio_id, "device ID", this.idRegex) ||
        !this.validateElemValue(this.insighio_key, "device Key", this.idRegex) ||
        !this.validateElemValue(this.insighio_channel, "channel ID", this.idRegex) ||
        !this.validateElemValue(this.insighio_control_channel, "control channel ID", this.idRegex)
      ) {
        return false
      }

      // Validate MQTT settings if secondary transmission is enabled
      if (this.enable_secondary_measurement_transmission) {
        if (!this.secondary_measurement_transmission_info.mqtt_url) {
          alert("MQTT URL is required when secondary measurement transmission is enabled")
          return false
        }
        if (!this.secondary_measurement_transmission_info.mqtt_port) {
          alert("MQTT Port is required when secondary measurement transmission is enabled")
          return false
        }
        if (!this.secondary_measurement_transmission_info.mqtt_topic) {
          alert("MQTT Topic is required when secondary measurement transmission is enabled")
          return false
        }
      }

      this.storeData()
      return true
    },
    storeData() {
      this.clearCookies()

      this.$storage.set("insighio-id", this.insighio_id)
      this.$storage.set("insighio-key", this.insighio_key)
      this.$storage.set("insighio-channel", this.insighio_channel)
      this.$storage.set("insighio-control-channel", this.insighio_control_channel)

      // Store secondary measurement transmission settings
      this.$storage.set(
        "enable-secondary-measurement-transmission",
        this.boolToPyStr(this.enable_secondary_measurement_transmission)
      )
      this.$storage.set("secondary-measurement-transmission-info", this.secondary_measurement_transmission_info)

      this.requestGoNext()
    }
  }
}
</script>
