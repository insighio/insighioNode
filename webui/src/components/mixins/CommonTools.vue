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
    this.initializeValues()
  },
  methods: {
    enableButtonsLocal() {
      this.disableButtons = false
    },

    disableButtonsLocal() {
      this.disableButtons = true
    },
    initializeValues() {},
    clearAllCookies() {
      console.log("this.$storage.keys(): ", this.$storage.keys())
      this.$storage.clear()

      console.log("this.$storage.keys() after: ", this.$storage.keys())
    },
    requestGoNext() {
      this.$emit("goNext")
    },
    requestGoBack() {
      this.$emit("goBack")
    },
    validateElemValue(val, message, idRegex) {
      if (val === undefined || val === null) {
        window.alert("Please enter field: " + message)
        return false
      }

      var value = val.trim()
      if (value == "" || (idRegex && !new RegExp(idRegex, "g").exec(value))) {
        window.alert("Please enter a valid " + message)
        return false
      }
      return true
    },
    getValueWithDefaults(val, defaultVal = undefined) {
      return val !== undefined && val !== null ? val : defaultVal
    },
    strToJSValue(strVal, defaultVal = undefined) {
      if (strVal === undefined || strVal === null) return defaultVal

      try {
        strVal = strVal ? strVal.toLowerCase() : strVal
      } catch (e) {}
      if (strVal === "undefined" || strVal === "" || strVal === "none") return defaultVal
      else if (strVal === "true") return true
      else if (strVal === "false") return false
      return strVal
    },
    boolToPyStr(val) {
      return val ? "True" : "False"
    },
    getJsonObjectFromCookies(cookieName) {
      const cookieValue = this.$storage.get(cookieName)

      // console.log("Cookie: " + cookieName + ", value: " + cookieValue + ", type: " + typeof cookieValue)
      if (cookieValue) {
        try {
          return JSON.parse(cookieValue)
        } catch (e) {
          //  console.error("Error parsing JSON from cookie:", e)
        }
      }
      return cookieValue
    }
  }
}
</script>

<style scoped>
.network {
  /* Add your component styles here */
}
</style>
