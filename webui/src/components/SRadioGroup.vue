<template>
  <div :class="'columns col-' + colsSum" style="padding-right: 0px; padding-left: 0px">
    <div :class="'col-' + colsLabel + ' col-sm-12'">
      <label class="form-label">{{ label }}</label>
    </div>
    <div :class="'col-' + colsInput + ' col-sm-12'">
      <label v-for="opt in valueOptions" :key="opt.value" class="form-radio">
        <input type="radio" :value="opt.value" v-model="internalValue" />
        <i class="form-icon"></i> {{ opt.label }}
      </label>
    </div>
    <br />
    <br />
  </div>
</template>

<script>
export default {
  name: "SRadioGroup",
  props: {
    value: {
      type: String,
      required: true
    },
    valueOptions: {
      type: Array,
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
