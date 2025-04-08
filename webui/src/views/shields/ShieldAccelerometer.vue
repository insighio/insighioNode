<template>
  <div class="form-group columns">
    <WebuiFooter @savePressed="validateMyForm" @backPressed="requestGoBack" />
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"
import WebuiFooter from "@/components/WebuiFooter.vue"

export default {
  name: "ShieldAccelerometer",
  mixins: [CommonTools],
  components: { WebuiFooter },
  methods: {
    // Add your component methods here
    validateMyForm() {
      this.requestGoNext()
    }
  }
}
</script>
