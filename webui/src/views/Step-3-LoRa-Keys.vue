<template>
  <div class="panel-body">
    <br />
    <div id="loader" class="loading loading-lg"></div>
    <div class="text-center">Set keys provided by the LoRa Server.</div>
    <br />
    <div class="container grid-lg">
      <div class="columns flex-centered">
        <div class="column col-xl-7 col-md-10 col-sm-12">
          <div class="form-group">
            <div class="columns">
              <SInput
                label="DEV_EUI"
                v-model:value="lora_dev_eui"
                @update:value="lora_dev_eui = $event"
                :colsLabel="3"
                :colsInput="9"
              />
              <div class="col-3 col-sm-12">
                <label class="form-label" for="input-app-eui"
                  >APP_EUI
                  <div class="popover popover-bottom">
                    <button class="btn btn-link">(Optional)</button>
                    <div class="popover-container">
                      <div class="card">
                        <div class="card-body">If left blank, default value "0000000000000001" will be used</div>
                      </div>
                    </div>
                  </div>
                </label>
              </div>
              <div class="col-9 col-sm-12">
                <input class="form-input constr-field" type="text" v-model="lora_app_eui" />
              </div>
              <br />
              <br />
              <SInput
                label="APP_KEY"
                v-model:value="lora_app_key"
                @update:value="lora_app_key = $event"
                :colsLabel="3"
                :colsInput="9"
              />
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
import SInput from "@/components/SInput.vue"
import WebuiFooter from "@/components/WebuiFooter.vue"

export default {
  name: "Step3LoRaKeys",
  mixins: [CommonTools],
  components: { SInput, WebuiFooter },
  data() {
    return {
      lora_dev_eui: "",
      lora_app_eui: "",
      lora_app_key: ""
    }
  },
  mounted() {
    // Add your mounted logic here
    this.initializeValues()
  },

  methods: {
    initializeValues() {
      this.lora_dev_eui = this.$cookies.get("lora-dev-eui")
      this.lora_app_eui = this.$cookies.get("lora-app-eui")
      this.lora_app_key = this.$cookies.get("lora-app-key")

      //      detectBoardChange(enableNavigationButtons)
    },
    clearCookies() {
      this.$cookies.remove("lora-dev-eui")
      this.$cookies.remove("lora-app-eui")
      this.$cookies.remove("lora-app-key")
    },
    storeData() {
      this.clearCookies()

      this.$cookies.set("lora-dev-eui", this.lora_dev_eui.trim())
      this.$cookies.set("lora-app-eui", this.lora_app_eui.trim())
      this.$cookies.set("lora-app-key", this.lora_app_key.trim())

      this.requestGoNext()
    },
    validateMyForm() {
      var euiRegex = "[0-9a-fA-F]{16}"
      var appKeyRegex = "[0-9a-fA-F]{32}"
      if (
        !this.validateElemValue(this.lora_dev_eui, "Dev EUI", euiRegex) ||
        !this.validateElemValue(this.lora_app_key, "App Key", appKeyRegex)
      )
        return false

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
