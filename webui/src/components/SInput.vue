<template>
  <div class="container">
    <div :class="'columns col-' + colsSum" style="padding-right: 0px; padding-left: 0px">
      <div :class="'column col-' + colsLabel + ' col-sm-12'">
        <label class="form-label">
          {{ label }}
          <button v-if="tooltip" class="btn btn-link tooltip" :data-tooltip="tooltip">
            <i class="icon icon-flag"></i>
          </button>
        </label>
      </div>
      <div :class="'column col-' + colsInput + ' col-sm-12'">
        <input
          id="inputField"
          :disabled="disabled"
          :type="inputType"
          class="form-input constr-field"
          v-model="internalValue"
          ref="inputField"
        />
      </div>
      <br />
      <br />
    </div>
  </div>
</template>

<script>
import SElementCommon from "./mixins/SElementCommon.vue"

export default {
  name: "SInput",
  mixins: [SElementCommon],
  props: {
    value: {
      type: [String, Number],
      default: "",
      required: true
    },
    inputType: {
      type: String,
      default: "text"
    }
  },
  methods: {
    focusInput() {
      this.$refs.inputField.focus()
    }
  }
}
</script>
