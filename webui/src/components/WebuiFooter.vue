<template>
  <div class="column col-12 wizard-actions">
    <button v-if="showBackButton" class="btn" type="button" @click="backPressed()">Back</button>
    <button v-if="showSaveButton" class="btn btn-primary" type="button" @click="savePressed()">
      Save &amp; continue <i class="icon icon-arrow-right" aria-hidden="true"></i>
    </button>
  </div>
</template>

<script>
export default {
  name: "WebuiFooter",
  props: {
    showBackButton: {
      type: Boolean,
      default: true,
      required: false
    },
    showSaveButton: {
      type: Boolean,
      default: true,
      required: false
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
  }
}
</script>
