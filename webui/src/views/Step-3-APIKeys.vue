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
              <div class="col-3 col-sm-12">
                <label class="form-label" for="input-id">ID</label>
              </div>
              <div class="col-9 col-sm-12">
                <input class="form-input constr-field" type="text" v-model="insighio_id" @paste="fillClipboardData" />
              </div>
              <br />
              <br />
              <div class="col-3 col-sm-12">
                <label class="form-label" for="input-key">KEY</label>
              </div>
              <div class="col-9 col-sm-12">
                <input class="form-input constr-field" type="text" v-model="insighio_key" @paste="fillClipboardData" />
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
                  @paste="fillClipboardData"
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
                  @paste="fillClipboardData"
                />
              </div>
              <br />
              <br />
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

export default {
  name: "ApiKeys",
  mixins: [CommonTools],
  components: { WebuiFooter },
  data() {
    return {
      // Add your component data here
      insighio_id: "",
      insighio_key: "",
      insighio_channel: "",
      insighio_control_channel: "",
      idRegex: "[0-9a-f]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12}"
    }
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
      this.$cookies.remove("insighio-id")
      this.$cookies.remove("insighio-key")
      this.$cookies.remove("insighio-channel")
      this.$cookies.remove("insighio-control-channel")
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

      this.storeData()
      return true
    },
    storeData() {
      this.clearCookies()

      this.$cookies.set("insighio-id", this.insighio_id)
      this.$cookies.set("insighio-key", this.insighio_key)
      this.$cookies.set("insighio-channel", this.insighio_channel)
      this.$cookies.set("insighio-control-channel", this.insighio_control_channel)

      this.requestGoNext()
    }
  }
}
</script>
