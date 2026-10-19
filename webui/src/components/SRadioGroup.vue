<template>
  <div class="container ui-mb-1">
    <div :class="'columns col-' + colsSum + ' ui-pr-0 ui-pl-0'">
      <div :class="'column col-' + colsLabel + ' col-sm-12'">
        <span class="form-label" :id="controlId + '-label'"
          >{{ label }}
          <button v-if="tooltip" class="btn btn-link tooltip" :data-tooltip="tooltip">
            <i class="icon icon-flag"></i>
          </button>
        </span>
      </div>
      <div :class="'column ol-' + colsInput + ' col-sm-12'" role="radiogroup" :aria-labelledby="controlId + '-label'">
        <label v-for="(opt, index) in valueOptions" :key="opt.value" class="form-radio">
          <input
            :id="controlId + '-' + index"
            :disabled="disabled"
            type="radio"
            :value="opt.value"
            v-model="internalValue"
          />
          <i class="form-icon"></i> {{ opt.label }}
        </label>
      </div>
    </div>
  </div>
</template>

<script>
import SElementCommon from "./mixins/SElementCommon.vue"

export default {
  name: "SRadioGroup",
  mixins: [SElementCommon],
  props: {
    value: {
      type: String,
      required: true
    },
    valueOptions: {
      type: Array,
      required: true
    }
  }
}
</script>
