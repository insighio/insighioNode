<template>
  <div class="form-group">
    <br />
    <div class="columns">
      <div class="col-12">
        <div class="divider text-center" data-content="Connection Configuration"></div>
      </div>
      <br />
      <br />
      <div class="col-3 col-sm-12">
        <label class="form-label" for="measurements">Region</label>
      </div>
      <div class="col-9 col-sm-12">
        <select class="form-select" v-model="lora_region">
          <option v-for="region in lora_region_list" :key="region" :value="region">{{ region }}</option>
        </select>
      </div>
      <br />
      <br />

      <div class="col-3 col-sm-12">
        <label class="form-label" for="input-example-cellular">DR</label>
      </div>
      <div class="col-9 col-sm-12">
        <input class="form-input constr-field" type="number" v-model="lora_dr" />
      </div>
      <br />
      <br />
      <div class="col-3 col-sm-12">
        <label class="form-label" for="input-example-cellular">TX Retries</label>
      </div>
      <div class="col-9 col-sm-12">
        <input class="form-input constr-field" type="number" v-model="lora_retries" />
      </div>
      <br />
      <br />
      <div class="col-3 col-sm-12">
        <label class="form-label" for="input-example-cellular">ADR</label>
      </div>
      <div class="col-9 col-sm-12">
        <label class="form-switch">
          <input type="checkbox" v-model="lora_adr" />
          <i class="form-icon"></i>
        </label>
      </div>
      <br />
      <br />
      <div class="col-3 col-sm-12">
        <label class="form-label" for="input-example-cellular">Confirmed</label>
      </div>
      <div class="col-9 col-sm-12">
        <label class="form-switch">
          <input type="checkbox" v-model="lora_confirmed" />
          <i class="form-icon"></i>
        </label>
      </div>
      <br />
      <br />
    </div>
    <div class="column col-12">
      <button class="btn btn-primary float-right" @click="validateMyForm()" id="save-button" style="margin-left: 30px">
        Save
      </button>
      <button class="btn btn-primary float-right" type="button" id="back-button" @click="requestGoBack">Back</button>
    </div>
    <br />
    <br />
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"

export default {
  name: "NetworkLoRa",
  mixins: [CommonTools],
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

      this.$cookies.set("lora-adr", this.boolElemToPyStr(this.lora_adr))
      this.$cookies.set("lora-confirmed", this.boolElemToPyStr(this.lora_confirmed))
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
