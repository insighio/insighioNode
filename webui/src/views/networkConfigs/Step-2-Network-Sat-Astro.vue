<template>
  <div class="form-group">
    <br />
    <div class="columns">
      <div class="col-12">
        <div class="divider text-center" data-content="Connection Configuration"></div>
      </div>
      <br />
      <br />
      <div class="col-4 col-sm-12">
        <label class="form-label"> Enable AstroNode DevKit </label>
      </div>
      <div class="col-8 col-sm-12">
        <label class="form-switch">
          <input type="checkbox" id="input-satAstroDevkitEnable" />
          <i class="form-icon"></i>
        </label>
      </div>
      <br />
      <br />
      <div class="col-4 col-sm-12">
        <label class="form-label" for="input-satAstroSSID">SSID</label>
      </div>
      <div class="col-8 col-sm-12">
        <input class="form-input constr-field" id="input-satAstroSSID" />
      </div>
      <br />
      <br />
      <div class="col-4 col-sm-12">
        <label class="form-label" for="input-satAstroPass">Password</label>
      </div>
      <div class="col-8 col-sm-12">
        <input class="form-input constr-field" id="input-satAstroPass" />
      </div>
      <br />
      <br />
      <div class="col-4 col-sm-12">
        <label class="form-label" for="input-satAstroToken">Access Token</label>
      </div>
      <div class="col-8 col-sm-12">
        <input class="form-input constr-field" id="input-satAstroToken" />
      </div>
      <br />
      <br />
    </div>
    <div class="column col-12">
      <button class="btn btn-primary float-right" onClick="validateMyForm()" id="save-button" style="margin-left: 30px">
        Save
      </button>
      <button class="btn btn-primary float-right" type="button" id="back-button" onclick="goBack()">Back</button>
    </div>
    <br />
    <br />
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"

export default {
  name: "NetworkSatAstro",
  mixins: [CommonTools],
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

      this.$cookies.set("sat-astro-devkit-en", this.boolElemToPyStr(this.dev_enable))
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
