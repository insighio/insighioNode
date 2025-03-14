<script>
import "@/assets/css/spectre-icons.min.css"
import "@/assets/css/spectre.min.css"
import "@/assets/css/style.css"

export default {
  data() {
    return {
      // Add your component data here
      mac: undefined,
      hw_module: undefined,
      disableButtons: false,
      isLoading: false
    }
  },
  mounted() {
    // Add your mounted logic here
  },
  methods: {
    enableButtonsLocal() {
      this.disableButtons = false
    },

    disableButtonsLocal() {
      this.disableButtons = true
    },

    clearAllCookies() {
      console.log("this.$cookies.keys(): ", this.$cookies.keys())
      this.$cookies.keys().forEach((key) => {
        this.$cookies.remove(key)
      })

      console.log("this.$cookies.keys() after: ", this.$cookies.keys())
    },
    requestGoNext() {
      this.$emit("goNext")
    },
    requestGoBack() {
      this.$emit("goBack")
    },
    validateElemValue(val, message, idRegex) {
      var value = val.trim()
      if (value == "" || (idRegex && !new RegExp(idRegex, "g").exec(value))) {
        window.alert("Please enter a valid " + message)
        return false
      }
      return true
    },
    getValueWithDefaults(val, defaultVal = undefined) {
      return val !== undefined ? val : defaultVal
    }
  },
  computed: {
    // Add your computed properties here
  }
}
</script>

<style scoped>
.network {
  /* Add your component styles here */
}
</style>
