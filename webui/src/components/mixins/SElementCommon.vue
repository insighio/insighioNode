<script>
export default {
  props: {
    value: {
      type: Boolean,
      required: true
    },
    label: {
      type: String,
      required: true
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
    disabled: {
      type: Boolean,
      default: false
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
