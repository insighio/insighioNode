<template>
  <div class="form-group">
    <br />
    <div class="columns">
      <SDivider label="Connection Configuration" />
      <SSwitch label="Enable AstroNode DevKit" v-model:value="dev_enable" @update:value="dev_enable = $event" />
      <SInput label="SSID" v-model:value="dev_ssid" @update:value="dev_ssid = $event" />
      <SInput label="Password" v-model:value="dev_pass" @update:value="dev_pass = $event" />
      <SInput label="Access Token" v-model:value="dev_token" @update:value="dev_token = $event" />
    </div>
    <WebuiFooter @savePressed="validateMyForm" @backPressed="requestGoBack" />
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"
import SSwitch from "@/components/SSwitch.vue"
import SInput from "@/components/SInput.vue"
import SDivider from "@/components/SDivider.vue"
import WebuiFooter from "@/components/WebuiFooter.vue"

export default {
  name: "NetworkSatAstro",
  mixins: [CommonTools],
  components: { SSwitch, SInput, SDivider, WebuiFooter },
  data() {
    return {
      // Add your component data here
      dev_ssid: "",
      dev_pass: "",
      dev_token: "",
      dev_enable: false
    }
  },
  mounted() {
    this.initializeValues()
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
