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
      if (val === undefined || val === null) return defaultVal
      else if (typeof val !== "string") return val

      try {
        val = val ? val.toLowerCase() : val
      } catch (e) {}
      if (val === "undefined" || val === "" || val === "none") return defaultVal
      else if (val === "true") return true
      else if (val === "false") return false
      return val
    },
    getJsonObjectFromCookies(cookieName) {
      const cookieValue = this.$cookies.get(cookieName)

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
