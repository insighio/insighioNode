<template>
  <div :class="'column col-' + colsSum" style="margin-bottom: 1rem">
    <div v-if="label" class="divider text-center" :data-content="label"></div>
    <div v-else class="divider"></div>
  </div>
</template>

<script>
export default {
  name: "SDivider",
  props: {
    label: {
      type: String,
      default: undefined
    },
    colsSum: {
      type: Number,
      default: 12
    }
  }
}
</script>
