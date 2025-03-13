<!--script setup>
import Step1Login from "@/components/Step-1-Login.vue"
import Step2Network from "@/components/Step-2-Network.vue"
import Step3APIKeys from "@/components/Step-3-APIKeys.vue"
import Step4Measurements from "@/components/Step-4-Measurements.vue"
import Step5Timing from "@/components/Step-5-Timing.vue"
import Step6Verify from "@/components/Step-6-Verify.vue"

import "@/assets/css/spectre.min.css"
import "@/assets/css/style.css"

const openReadmeInEditor = () => fetch("/__open-in-editor?file=README.md")
let tabActive = 0

const tabs = ["Login", "Network", "API Keys", "Measurements", "Timing", "Verify"]

const goToNextStep = () => {
  console.log("goToNextStep")
  tabActive += 1

  console.log("goToNextStep: ", tabActive)
}
</script-->

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
        <Step3APIKeys v-else-if="tabActive === 2" @goNext="goToNextStep" @goBack="goToPreviousStep" />
        <Step4Measurements v-else-if="tabActive === 3" @goNext="goToNextStep" @goBack="goToPreviousStep" />
        <Step5Timing v-else-if="tabActive === 4" @goNext="goToNextStep" @goBack="goToPreviousStep" />
        <Step6Verify v-else-if="tabActive === 5" @goNext="goToNextStep" @goBack="goToPreviousStep" />
      </div>
    </div>
  </div>
</template>

<script>
import Step1Login from "@/components/Step-1-Login.vue"
import Step2Network from "@/components/Step-2-Network.vue"
import Step3APIKeys from "@/components/Step-3-APIKeys.vue"
import Step4Measurements from "@/components/Step-4-Measurements.vue"
import Step5Timing from "@/components/Step-5-Timing.vue"
import Step6Verify from "@/components/Step-6-Verify.vue"

import "@/assets/css/spectre.min.css"

export default {
  name: "MainPage",
  components: { Step1Login, Step2Network, Step3APIKeys, Step4Measurements, Step5Timing, Step6Verify },
  data() {
    return {
      tabs: ["Login", "Network", "API Keys", "Measurements", "Timing", "Verify"],
      tabActive: 0,
    }
  },
  methods: {
    goToNextStep() {
      this.tabActive += 1

      console.log("goToNextStep: ", this.tabActive)
    },
    goToPreviousStep() {
      this.tabActive -= 1

      console.log("goToPrevStep: ", this.tabActive)
    },
  },
  computed: {
    // Add your computed properties here
  },
  mounted() {
    // Add your mounted logic here
  },
  setup() {
    console.log("accessing setup")
  },
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
