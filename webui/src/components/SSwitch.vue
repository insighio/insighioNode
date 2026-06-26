<template>
  <div class="container ui-mb-1">
    <div :class="'columns col-' + colsSum + ' ui-pr-0 ui-pl-0'">
      <div :class="'column col-' + colsLabel + ' col-sm-12'">
        <label class="form-label"
          >{{ label }}
          <button v-if="tooltip" class="btn btn-link tooltip" :data-tooltip="tooltip">
            <i class="icon icon-flag"></i>
          </button>
        </label>
      </div>
      <div :class="'column col-' + colsInput + ' col-sm-12'">
        <label class="form-switch">
          <input :id="label" :disabled="disabled" type="checkbox" v-model="internalValue" />
          <i class="form-icon"></i>
        </label>
      </div>
    </div>
  </div>
</template>

<script>
import SElementCommon from "./mixins/SElementCommon.vue"

export default {
  name: "SSwitch",
  mixins: [SElementCommon]
}
</script>
