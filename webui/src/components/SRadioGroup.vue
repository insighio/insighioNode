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
      <div :class="'column ol-' + colsInput + ' col-sm-12'">
        <label v-for="opt in valueOptions" :key="opt.value" class="form-radio">
          <input :disabled="disabled" type="radio" :value="opt.value" v-model="internalValue" />
          <i class="form-icon"></i> {{ opt.label }}
        </label>
      </div>
      <br />
      <br />
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
