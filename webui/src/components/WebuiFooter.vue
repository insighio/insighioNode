<template>
  <div class="column col-12">
    <button class="btn btn-primary float-right" @click="savePressed()" style="margin-left: 30px">Save</button>
    <button class="btn btn-primary float-right" type="button" @click="backPressed()">Back</button>
    <br />
    <br />
    <br />
    <br />
    <br />
    <br />
  </div>
</template>

<script>
export default {
  name: "WebuiFooter",
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
