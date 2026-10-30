<template>
  <div class="panel-body login-panel">
    <div class="container">
      <div class="columns flex-centered">
        <div class="column col-6 col-xl-8 col-md-10 col-sm-12">
          <form class="form-group login-form" @submit.prevent="checkPassword" :aria-busy="isLoggingIn">
            <label class="form-label" for="input-username">Username</label>
            <input
              id="input-username"
              class="form-input constr-field"
              type="text"
              placeholder="Username"
              v-model="username"
              autocomplete="username"
              autocapitalize="none"
              spellcheck="false"
              required
              :disabled="isLoggingIn"
            />
            <label class="form-label" for="input-password">Password</label>
            <input
              id="input-password"
              class="form-input constr-field"
              type="password"
              placeholder="Password"
              v-model="password"
              autocomplete="current-password"
              required
              :disabled="isLoggingIn"
            />
            <p v-if="loginError" class="toast toast-error ui-mt-1" role="alert">{{ loginError }}</p>
            <div class="flex-centered ui-mt-1 ui-mb-1">
              <button class="btn btn-primary constr-field" type="submit" :disabled="isLoggingIn">
                <span v-if="isLoggingIn">Logging in...</span>
                <span v-else>Login</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"
import { fetchInternal } from "@/js/utils.js"

export default {
  name: "Step1Login",
  mixins: [CommonTools],
  data() {
    return {
      username: "",
      password: "",
      isLoggingIn: false,
      loginError: ""
    }
  },
  computed: {
    // Add your computed properties here
  },
  mounted() {
    // Add your mounted logic here
    this.checkAlreadyLoggedIn()
  },
  methods: {
    checkPassword() {
      if (this.isLoggingIn) return false
      this.loginError = ""
      if (!this.username || !this.password) {
        this.loginError = "Please enter your username and password."
        return false
      }

      this.isLoggingIn = true

      fetchInternal("/login", 10000, "POST", {
        username: this.username,
        password: this.password
      })
        .then((data) => {
          this.isLoggingIn = false
          if (data.success) {
            this.clearAllCookies()
            this.$storage.set("session", "true")
            this.requestGoNext()
          } else {
            this.loginError = data.message || "Incorrect username or password. Please try again."
          }
        })
        .catch((err) => {
          this.isLoggingIn = false
          console.log("Login error:", err)
          this.loginError = "Could not sign in. Check your device connection and try again."
        })

      return false
    },
    checkAlreadyLoggedIn() {
      if (this.$storage.isKey("session")) {
        this.requestGoNext()
      }
    }
  }
}
</script>
