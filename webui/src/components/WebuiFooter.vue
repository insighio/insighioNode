<template>
  <div class="column col-12 ui-mb-3 ui-mt-2">
    <button v-if="showSaveButton" class="btn btn-primary float-right" @click="savePressed()" style="margin-left: 30px">
      Save
    </button>
    <button v-if="showBackButton" class="btn btn-primary float-right" type="button" @click="backPressed()">Back</button>
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
