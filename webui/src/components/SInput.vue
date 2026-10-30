<template>
  <div class="container ui-mb-1">
    <div :class="'columns col-' + colsSum + ' ui-pr-0 ui-pl-0'">
      <div :class="'column col-' + colsLabel + ' col-sm-12'">
        <label class="form-label" :for="controlId">
          {{ label }}
        </label>
        <details v-if="tooltip" class="field-help">
          <summary :aria-label="`Help for ${label}`">More info</summary>
          <p>{{ tooltip }}</p>
        </details>
      </div>
      <div :class="'column col-' + colsInput + ' col-sm-12'">
        <input
          :id="controlId"
          :disabled="disabled"
          :type="inputType"
          class="form-input constr-field"
          v-model="internalValue"
          :placeholder="placeholder"
          ref="inputField"
        />
      </div>
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
    },
    placeholder: {
      type: String,
      default: ""
    }
  },
  methods: {
    focusInput() {
      this.$refs.inputField.focus()
    }
  }
}
</script>
