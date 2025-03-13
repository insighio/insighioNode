<template>
  <div class="panel-body">
    <br />
    <div class="text-center">
      Set API keys that were generated during device creation in console.insigh.io.
      <div class="popover popover-bottom">
        <button class="btn btn-link">Tip: Autofill</button>
        <div class="popover-container">
          <div class="card">
            <div class="card-header">
              <div class="card-title h5">Auto fill fields</div>
            </div>
            <div class="card-body">
              In <a href="https://console.insigh.io/devices/list">Device List view</a> select the required device and
              press Options <img src="@/assets/img/devOpt.png" style="margin-bottom: -5px" /> -> JSON
              <img src="@/assets/img/copy.png" style="margin-bottom: -5px" />. Then paste in any of the input fields and
              the contents will be auto-filled.
            </div>
          </div>
        </div>
      </div>
    </div>
    <br />
    <div class="container grid-lg">
      <div class="columns flex-centered">
        <div class="column col-xl-7 col-md-10 col-sm-12">
          <div class="form-group">
            <div class="columns">
              <div class="col-3 col-sm-12">
                <label class="form-label" for="input-id">ID</label>
              </div>
              <div class="col-9 col-sm-12">
                <input
                  class="form-input constr-field"
                  type="text"
                  v-model="insighio_id"
                  @paste.prevent="fillClipboardData"
                />
              </div>
              <br />
              <br />
              <div class="col-3 col-sm-12">
                <label class="form-label" for="input-key">KEY</label>
              </div>
              <div class="col-9 col-sm-12">
                <input
                  class="form-input constr-field"
                  type="text"
                  v-model="insighio_key"
                  @paste.prevent="fillClipboardData"
                />
              </div>
              <br />
              <br />
              <div class="col-3 col-sm-12">
                <label class="form-label" for="input-channel">Data Channel</label>
              </div>
              <div class="col-9 col-sm-12">
                <input
                  class="form-input constr-field"
                  type="text"
                  v-model="insighio_channel"
                  @paste.prevent="fillClipboardData"
                />
              </div>
              <br />
              <br />
              <div class="col-3 col-sm-12">
                <label class="form-label" for="input-controlChannel">Control Channel</label>
              </div>
              <div class="col-9 col-sm-12">
                <input
                  class="form-input constr-field"
                  type="text"
                  v-model="insighio_control_channel"
                  @paste.prevent="fillClipboardData"
                />
              </div>
              <br />
              <br />
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
              <button class="btn btn-primary float-right" type="button" id="back-button" @click="requestGoBack()">
                Back
              </button>
            </div>
            <br />
            <br />
            <br />
            <br />
            <br />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"

export default {
  name: "ApiKeys",
  mixins: [CommonTools],
  data() {
    return {
      // Add your component data here
      insighio_id: "",
      insighio_key: "",
      insighio_channel: "",
      insighio_control_channel: ""
    }
  },
  computed: {
    // Add your computed properties here
  },
  mounted() {
    // Add your mounted logic here
    // this.initializeValues()
  },
  methods: {
    initializeValues() {
      this.insighio_id = this.$cookies.get("insighio-id")
      this.insighio_key = this.$cookies.get("insighio-key")
      this.insighio_channel = this.$cookies.get("insighio-channel")
      this.insighio_control_channel = this.$cookies.get("insighio-control-channel")

      //detectBoardChange(enableNavigationButtons)
    },
    fillClipboardData(evt) {
      this.$nextTick(() => {
        try {
          var obj = JSON.parse(evt.clipboardData.getData("text"))
          this.insighio_id = obj.id
          this.insighio_key = obj.key
          this.insighio_channel = obj.channel
          this.insighio_control_channel = obj.controlChannel
        } catch (e) {
          console.log("Error parsing clipboard data: ", e)
        }
      })
    },
    clearCookies() {
      this.$cookies.remove("insighio-id")
      this.$cookies.remove("insighio-key")
      this.$cookies.remove("insighio-channel")
      this.$cookies.remove("insighio-channel-control")
    },
    validateMyForm() {
      var idRegex = "[0-9a-f]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12}"
      if (
        !this.validateElemValue("input-id", "device ID", idRegex) ||
        !this.validateElemValue("input-key", "device Key", idRegex) ||
        !this.validateElemValue("input-channel", "channel ID", idRegex)
      )
        return false

      this.storeData()
      return true
    },
    storeData() {
      this.disableNavigationButtons()
      this.clearCookies()

      this.$cookies.set("insighio-id", document.getElementById("input-id").value.trim())
      this.$cookies.set("insighio-key", document.getElementById("input-key").value.trim())
      this.$cookies.set("insighio-channel", document.getElementById("input-channel").value.trim())
      this.$cookies.set("insighio-control-channel", document.getElementById("input-control-channel").value.trim())

      //redirectTo("step-5-measurements.html")
      this.enableNavigationButtons()
    }
  }
}
</script>

<style scoped>
.network {
  /* Add your component styles here */
}
</style>
