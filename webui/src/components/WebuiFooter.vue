<template>
  <div class="column col-12">
    <button class="btn btn-primary float-right" @click="savePressed()" style="margin-left: 30px">Save</button>
    <button class="btn btn-primary float-right" type="button" @click="backPressed()">Back</button>
    <br />
    <br />
  </div>
</template>

<script>
export default {
  name: "WebuiFooter",
  data() {
    return {
      // Add your component data here
    }
  },
  methods: {
    // Add your component methods here
    savePressed() {
      this.$emit("savePressed")
    },
    backPressed() {
      this.$emit("backPressed")
    }
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
