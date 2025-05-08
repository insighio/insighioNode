<template>
  <div class="container">
    <div :class="'columns col-' + colsSum" style="padding-right: 0px; padding-left: 0px">
      <div :class="'col-' + colsLabel + ' col-sm-12'">
        <label class="form-label"
          >{{ label }}
          <button v-if="tooltip" class="btn btn-link tooltip" :data-tooltip="tooltip">
            <i class="icon icon-flag"></i>
          </button>
        </label>
      </div>
      <div :class="'col-' + colsInput + ' col-sm-12'">
        <label class="form-switch">
          <input :disabled="disabled" type="checkbox" v-model="internalValue" />
          <i class="form-icon"></i>
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
  name: "SSwitch",
  mixins: [SElementCommon]
}
</script>
