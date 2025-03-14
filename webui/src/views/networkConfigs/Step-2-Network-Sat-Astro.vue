<template>
  <div class="form-group">
    <br />
    <div class="columns">
      <div class="col-12">
        <div class="divider text-center" data-content="Connection Configuration"></div>
      </div>
      <br />
      <br />
      <SSwitch label="Enable AstroNode DevKit" v-model:value="dev_enable" @update:value="dev_enable = $event" />
      <br />
      <br />
      <SInput label="SSID" v-model:value="dev_ssid" @update:value="dev_ssid = $event" />
      <br />
      <br />
      <SInput label="Password" v-model:value="dev_pass" @update:value="dev_pass = $event" />
      <br />
      <br />
      <SInput label="Access Token" v-model:value="dev_token" @update:value="dev_token = $event" />
      <br />
      <br />
    </div>
    <div class="column col-12">
      <button class="btn btn-primary float-right" @click="validateMyForm()" id="save-button" style="margin-left: 30px">
        Save
      </button>
      <button class="btn btn-primary float-right" type="button" id="back-button" @click="requestGoBack()">Back</button>
    </div>
    <br />
    <br />
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"
import SSwitch from "@/components/SSwitch.vue"
import SInput from "@/components/SInput.vue"

export default {
  name: "NetworkSatAstro",
  mixins: [CommonTools],
  components: { SSwitch, SInput },
  data() {
    return {
      // Add your component data here
      dev_ssid: "",
      dev_pass: "",
      dev_token: "",
      dev_enable: false
    }
  },
  computed: {
    // Add your computed properties here
  },

  methods: {
    initializeValues() {
      this.dev_ssid = this.$cookies.get("sat-astro-devkit-ssid")
      this.dev_pass = this.$cookies.get("sat-astro-devkit-pass")
      this.dev_token = this.$cookies.get("sat-astro-devkit-token")

      this.dev_enable = this.strToJSValue(this.$cookies.get("sat-astro-devkit-en"), false)
    },
    clearCookies() {
      this.$cookies.remove("sat-astro-devkit-en")
      this.$cookies.remove("sat-astro-devkit-ssid")
      this.$cookies.remove("sat-astro-devkit-pass")
      this.$cookies.remove("sat-astro-devkit-token")
      this.$cookies.remove("network")
    },
    storeData() {
      this.clearCookies()

      this.$cookies.set("network", "satellite")

      this.$cookies.set("sat-astro-devkit-en", this.boolToPyStr(this.dev_enable))
      this.$cookies.set("sat-astro-devkit-ssid", this.dev_ssid)
      this.$cookies.set("sat-astro-devkit-pass", this.dev_pass)
      this.$cookies.set("sat-astro-devkit-token", this.dev_token)

      this.requestGoNext()
    },
    validateMyForm() {
      this.storeData()
      return true
    }
  }
}
</script>

<style scoped>
.network {
  /* Add your component styles here */
}
</style>
