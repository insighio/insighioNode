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
            <div class="password-field">
              <input
                id="input-password"
                class="form-input constr-field"
                :type="showPassword ? 'text' : 'password'"
                placeholder="Password"
                v-model="password"
                autocomplete="current-password"
                autocapitalize="none"
                spellcheck="false"
                required
                :disabled="isLoggingIn"
              />
              <button
                type="button"
                class="password-toggle"
                :aria-label="showPassword ? 'Hide password' : 'Show password'"
                :aria-pressed="showPassword"
                aria-controls="input-password"
                :title="showPassword ? 'Hide password' : 'Show password'"
                :disabled="isLoggingIn"
                @click="showPassword = !showPassword"
              >
                <svg
                  v-if="showPassword"
                  viewBox="0 0 24 24"
                  width="22"
                  height="22"
                  aria-hidden="true"
                  focusable="false"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                  <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                  <path d="M14.12 14.12a3 3 0 1 1-4.24-4.24" />
                  <line x1="1" y1="1" x2="23" y2="23" />
                </svg>
                <svg
                  v-else
                  viewBox="0 0 24 24"
                  width="22"
                  height="22"
                  aria-hidden="true"
                  focusable="false"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
              </button>
            </div>
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
      showPassword: false,
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
