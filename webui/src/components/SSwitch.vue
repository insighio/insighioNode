<template>
  <div class="container ui-mb-1 s-field s-switch">
    <div :class="'columns col-' + colsSum + ' ui-pr-0 ui-pl-0'">
      <div :class="'column s-switch-label col-' + colsLabel + ' col-sm-12'">
        <label class="form-label" :for="controlId">{{ label }} </label>
        <details v-if="tooltip" class="field-help">
          <summary :aria-label="`Help for ${label}`">More info</summary>
          <p>{{ tooltip }}</p>
        </details>
      </div>
      <div :class="'column s-switch-control col-' + colsInput + ' col-sm-12'">
        <label class="form-switch">
          <input :id="controlId" :disabled="disabled" type="checkbox" v-model="internalValue" />
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

<style scoped>
@media (max-width: 600px) {
  /* Spectre's col-sm-12 stacks label and switch; use a grid so they share a row and help spans below. */
  .s-switch {
    margin-bottom: 0.4rem;
  }

  .s-switch > .columns {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    column-gap: 0.75rem;
    align-items: start;
    margin: 0;
  }

  .s-switch .s-switch-label {
    display: contents;
  }

  .s-switch .s-switch-label .form-label {
    grid-column: 1;
    grid-row: 1;
    padding-bottom: 0.3rem;
  }

  .s-switch .s-switch-label .field-help {
    grid-column: 1 / -1;
    grid-row: 2;
  }

  .s-switch .s-switch-control {
    grid-column: 2;
    grid-row: 1;
    width: auto;
    padding: 0;
  }

  .s-switch .form-switch {
    margin: 0;
    padding-right: 0;
  }

  /* Center the toggle on the label's first line (0.3rem padding + half of the 1.2rem line height). */
  .s-switch .form-switch .form-icon {
    top: 0.45rem;
  }
}
</style>
