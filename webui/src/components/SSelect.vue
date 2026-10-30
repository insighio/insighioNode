<template>
  <div class="container ui-mb-1">
    <div :class="'columns col-' + colsSum + ' ui-pr-0 ui-pl-0'">
      <div :class="'column col-' + colsLabel + ' col-sm-12'">
        <label class="form-label" :for="controlId">{{ label }} </label>
        <details v-if="tooltip" class="field-help">
          <summary :aria-label="`Help for ${label}`">More info</summary>
          <p>{{ tooltip }}</p>
        </details>
      </div>
      <div :class="'column col-' + colsInput + ' col-sm-12'">
        <select :id="controlId" :disabled="disabled" class="form-select" v-model="internalValue">
          <option v-for="opt in valueOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script>
import SElementCommon from "./mixins/SElementCommon.vue"

export default {
  name: "SSelect",
  mixins: [SElementCommon],
  props: {
    value: {
      type: [String, Number, Boolean],
      required: true
    },
    valueOptions: {
      type: Array,
      required: true
    }
  }
}
</script>
