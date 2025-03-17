<template>
  <div class="form-group">
    <br />
    <div class="columns">
      <SDivider label="Connection Configuration" />

      <SSelect
        label="Region"
        v-model:value="lora_region"
        @update:value="lora_region = $event"
        :valueOptions="lora_region_list"
        :colsLabel="3"
        :colsInput="9"
      />

      <SInput
        label="DR"
        v-model:value="lora_dr"
        inputType="number"
        @update:value="lora_dr = $event"
        :colsLabel="3"
        :colsInput="9"
      />

      <SInput
        label="TX Retries"
        v-model:value="lora_retries"
        inputType="number"
        @update:value="lora_retries = $event"
        :colsLabel="3"
        :colsInput="9"
      />

      <SSwitch label="ADR" v-model:value="lora_adr" @update:value="lora_adr = $event" :colsLabel="3" :colsInput="9" />

      <SSwitch
        label="Confirmed"
        v-model:value="lora_confirmed"
        @update:value="lora_confirmed = $event"
        :colsLabel="3"
        :colsInput="9"
      />
    </div>
    <WebuiFooter @savePressed="validateMyForm" @backPressed="requestGoBack" />
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"
import SInput from "@/components/SInput.vue"
import SSelect from "@/components/SSelect.vue"
import SDivider from "@/components/SDivider.vue"
import SSwitch from "@/components/SSwitch.vue"
import WebuiFooter from "@/components/WebuiFooter.vue"

export default {
  name: "NetworkLoRa",
  mixins: [CommonTools],
  components: { SInput, SSelect, SDivider, SSwitch, WebuiFooter },
  data() {
    return {
      // Add your component data here
      lora_region_list: [
        "EU433",
        "CN470",
        "RU864",
        "IN865",
        "EU868",
        "US915",
        "AU915",
        "LA915",
        "KR920",
        "AS923-1",
        "AS923-2",
        "AS923-3",
        "AS923-4"
      ],
      lora_region: "EU868",
      lora_dr: 5,
      lora_retries: 1,
      lora_adr: true,
      lora_confirmed: true
    }
  },

  methods: {
    initializeValues() {
      this.lora_adr = this.strToJSValue(this.$cookies.get("lora-adr"), true)
      this.lora_confirmed = this.strToJSValue(this.$cookies.get("lora-confirmed"), true)

      this.lora_region = this.getValueWithDefaults(this.$cookies.get("lora-region"), "EU868")
      this.lora_dr = this.getValueWithDefaults(this.$cookies.get("lora-dr"), 5)
      this.lora_retries = this.getValueWithDefaults(this.$cookies.get("lora-retries"), 1)

      //detectBoardChange(enableNavigationButtons)
    },
    clearCookies() {
      this.$cookies.remove("lora-adr")
      this.$cookies.remove("lora-confirmed")
      this.$cookies.remove("lora-dr")
      this.$cookies.remove("lora-region")
      this.$cookies.remove("lora-retries")
      this.$cookies.remove("network")
      this.$cookies.remove("protocol")
    },
    storeData() {
      this.clearCookies()
      this.$cookies.set("network", "lora")

      this.$cookies.set("lora-adr", this.boolToPyStr(this.lora_adr))
      this.$cookies.set("lora-confirmed", this.boolToPyStr(this.lora_confirmed))
      this.$cookies.set("lora-dr", this.lora_dr)
      this.$cookies.set("lora-region", this.lora_region)
      this.$cookies.set("lora-retries", this.lora_retries)

      this.requestGoNext()
    },
    validateMyForm() {
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
