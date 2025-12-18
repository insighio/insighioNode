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
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"
import SInput from "@/components/SInput.vue"
import SSelect from "@/components/SSelect.vue"
import SDivider from "@/components/SDivider.vue"
import SSwitch from "@/components/SSwitch.vue"

export default {
  name: "NetworkLoRa",
  mixins: [CommonTools],
  components: { SInput, SSelect, SDivider, SSwitch },
  data() {
    return {
      // Add your component data here
      lora_region_list: [
        { value: "EU433", label: "EU433" },
        { value: "CN470", label: "CN470" },
        { value: "RU864", label: "RU864" },
        { value: "IN865", label: "IN865" },
        { value: "EU868", label: "EU868" },
        { value: "US915", label: "US915" },
        { value: "AU915", label: "AU915" },
        { value: "LA915", label: "LA915" },
        { value: "KR920", label: "KR920" },
        { value: "AS923-1", label: "AS923-1" },
        { value: "AS923-2", label: "AS923-2" },
        { value: "AS923-3", label: "AS923-3" },
        { value: "AS923-4", label: "AS923-4" }
      ],
      lora_region: "EU868",
      lora_dr: 5,
      lora_retries: 1,
      lora_adr: true,
      lora_confirmed: true
    }
  },
  mounted() {
    this.initializeValues()
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
    storeData() {
      this.$cookies.set("network", "lora")

      this.$cookies.set("lora-adr", this.boolToPyStr(this.lora_adr))
      this.$cookies.set("lora-confirmed", this.boolToPyStr(this.lora_confirmed))
      this.$cookies.set("lora-dr", this.lora_dr)
      this.$cookies.set("lora-region", this.lora_region)
      this.$cookies.set("lora-retries", this.lora_retries)
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
