<template>
  <div class="container">
    <div :class="'columns col-' + colsSum" style="padding-right: 0px; padding-left: 0px">
      <div :class="'col-' + colsLabel + ' col-sm-12'">
        <label class="form-label">{{ label }}</label>
      </div>
      <div :class="'col-' + colsInput + ' col-sm-12'">
        <label class="form-switch">
          <input type="checkbox" v-model="internalValue" />
          <i class="form-icon"></i>
        </label>
      </div>
      <br />
      <br />
    </div>
  </div>
</template>

<script>
export default {
  name: "SSwitch",
  props: {
    value: {
      type: Boolean,
      required: true
    },
    label: {
      type: String,
      required: true
    },
    colsSum: {
      type: Number,
      default: 12
    },
    colsLabel: {
      type: Number,
      default: 4
    },
    colsInput: {
      type: Number,
      default: 8
    }
  },
  emits: ["update:value"],
  computed: {
    internalValue: {
      get() {
        return this.value
      },
      set(val) {
        this.$emit("update:value", val)
      }
    }
  }
}
</script>

<style scoped>
.network {
  /* Add your component styles here */
}
</style>
