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
  data() {
    return {
      // Add your component data here
    }
  },
  methods: {
    // Add your component methods here
  },
  computed: {
    // Add your computed properties here
  },
  mounted() {
    // Add your mounted logic here
  }
}
</script>

<style scoped>
.network {
  /* Add your component styles here */
}
</style>
