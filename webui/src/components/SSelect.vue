<template>
  <div class="container">
    <div :class="'columns col-' + colsSum" style="padding-right: 0px; padding-left: 0px">
      <div :class="'column col-' + colsLabel + ' col-sm-12'">
        <label class="form-label"
          >{{ label }}
          <button v-if="tooltip" class="btn btn-link tooltip" :data-tooltip="tooltip">
            <i class="icon icon-flag"></i>
          </button>
        </label>
      </div>
      <div :class="'column col-' + colsInput + ' col-sm-12'">
        <select :disabled="disabled" class="form-select" v-model="internalValue">
          <option v-for="opt in valueOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </div>
      <br />
      <br />
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
