<template>
  <div class="container">
    <div :class="'columns col-' + colsSum" style="padding-right: 0px; padding-left: 0px">
      <div :class="'col-' + colsLabel + ' col-sm-12'">
        <label class="form-label">
          {{ label }}
          <button v-if="tooltip" class="btn btn-link tooltip" :data-tooltip="tooltip">
            <i class="icon icon-flag"></i>
          </button>
        </label>
      </div>
      <div :class="'col-' + colsInput + ' col-sm-12'">
        <input :type="inputType" class="form-input constr-field" v-model="internalValue" />
      </div>
      <br />
      <br />
    </div>
  </div>
</template>

<script>
export default {
  name: "SInput",
  props: {
    value: {
      type: [String, Number],
      default: "",
      required: true
    },
    label: {
      type: String,
      required: true
    },
    inputType: {
      type: String,
      default: "text"
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
    },
    tooltip: {
      type: String,
      default: undefined
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
