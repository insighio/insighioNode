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
      isLoading: false,
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
      for (let key in this.$cookies.keys()) {
        this.$cookies.remove(key)
      }
    },
    requestGoNext() {
      this.$emit("goNext")
    },
    requestGoBack() {
      this.$emit("goBack")
    },
  },
  computed: {
    // Add your computed properties here
  },
}
</script>

<style scoped>
.network {
  /* Add your component styles here */
}
</style>
