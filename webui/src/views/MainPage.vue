<template>
  <div>
    <img src="@/assets/img/logo.png" class="img-responsive px-2 py-2 img-center" />
    <div class="panel panel-custom">
      <div class="panel-header">
        <div class="panel-title text-center">Welcome to insigh.io device configuration.</div>
      </div>

      <div class="columns">
        <div class="panel-nav col-12 hide-sm">
          <br />

          <ul class="step">
            <li v-for="tab in tabs" class="step-item" :key="tab" :class="{ active: tabActive === tabs.indexOf(tab) }">
              <a>{{ tab }}</a>
            </li>
          </ul>
        </div>
      </div>

      <div>
        <Step1Login v-if="tabActive === 0" @goNext="goToNextStep" />
        <Step2Network v-else-if="tabActive === 1" @goNext="goToNextStep" @goBack="goToPreviousStep" />
        <Step3APIKeys
          v-else-if="tabActive === 2 && networkTech !== 'lora'"
          @goNext="goToNextStep"
          @goBack="goToPreviousStep"
        />
        <Step3LoRaKeys
          v-else-if="tabActive === 2 && networkTech === 'lora'"
          @goNext="goToNextStep"
          @goBack="goToPreviousStep"
        />

        <Step4Measurements v-else-if="tabActive === 3" @goNext="goToNextStep" @goBack="goToPreviousStep" />
        <Step5Timing v-else-if="tabActive === 4" @goNext="goToNextStep" @goBack="goToPreviousStep" />
        <Step6Verify v-else-if="tabActive === 5" @goNext="goToNextStep" @goBack="goToPreviousStep" />
        <Step7Apply v-else-if="tabActive === 6" @start-over="goToStart" />
      </div>
    </div>
  </div>
</template>

<script>
import "@/assets/css/spectre.min.css"
import Step1Login from "@/views/Step-1-Login.vue"
import Step2Network from "@/views/Step-2-Network.vue"
import Step3APIKeys from "@/views/Step-3-APIKeys.vue"
import Step3LoRaKeys from "@/views/Step-3-LoRa-Keys.vue"
import Step4Measurements from "@/views/Step-4-Measurements.vue"
import Step5Timing from "@/views/Step-5-Timing.vue"
import Step6Verify from "@/views/Step-6-Verify.vue"
import Step7Apply from "@/views/Step-7-apply.vue"

export default {
  name: "MainPage",
  components: {
    Step1Login,
    Step2Network,
    Step3APIKeys,
    Step3LoRaKeys,
    Step4Measurements,
    Step5Timing,
    Step6Verify,
    Step7Apply
  },
  data() {
    return {
      tabs: ["Login", "Network", "API Keys", "Measurements", "Timing", "Verify", "Apply"],
      tabActive: -1,
      networkTech: ""
    }
  },
  mounted() {
    let storedActiveTab = this.$cookies.get("activeTab")

    console.log("storedActiveTab: ", storedActiveTab)
    if (storedActiveTab !== undefined && storedActiveTab !== null) this.tabActive = parseInt(storedActiveTab)
    else {
      this.tabActive = 0
      this.$cookies.set("activeTab", this.tabActive)
    }

    this.networkTech = this.$cookies.get("network")
  },
  methods: {
    goToNextStep() {
      this.networkTech = this.$cookies.get("network")

      this.tabActive += 1

      this.$cookies.set("activeTab", this.tabActive)

      console.log("goToNextStep: ", this.tabActive)
      //networkTech
    },
    goToPreviousStep() {
      this.tabActive -= 1

      this.$cookies.set("activeTab", this.tabActive)

      console.log("goToPrevStep: ", this.tabActive)
    },
    goToStart() {
      this.tabActive = 1
      this.$cookies.set("activeTab", this.tabActive)
      const savedSession = this.$cookies.get("session")
      this.$cookies.keys().forEach((cookie) => this.$cookies.remove(cookie))
      this.$cookies.set("session", savedSession)
    }
  },
  setup() {
    console.log("accessing setup")
  }
}
</script>

<style scoped>
.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.vue:hover {
  filter: drop-shadow(0 0 2em #42b883aa);
}
</style>
