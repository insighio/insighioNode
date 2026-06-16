<template>
  <div class="panel-body" style="padding-top: 1rem">
    <hr />
    <div class="container">
      <div class="columns flex-centered">
        <div class="column col-6 col-xl-8 col-md-10 col-sm-12">
          <div class="form-group">
            <label class="form-label" for="input-example-1">Username</label>
            <input
              class="form-input constr-field"
              type="text"
              placeholder="Username"
              v-model="username"
              @keyup.enter="checkPassword()"
            />
            <label class="form-label" for="input-example-1">Password</label>
            <input
              class="form-input constr-field"
              type="password"
              placeholder="Password"
              v-model="password"
              @keyup.enter="checkPassword()"
            />
            <div class="flex-centered" style="margin-top: 1rem">
              <button class="btn btn-primary constr-field" @click="checkPassword()" :disabled="isLoggingIn">
                <span v-if="isLoggingIn">Logging in...</span>
                <span v-else>Login</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import "@/assets/css/spectre.min.css"
import "@/assets/css/style.css"
import CommonTools from "@/components/mixins/CommonTools.vue"
import { fetchInternal } from "@/js/utils.js"

export default {
  name: "Step1Login",
  mixins: [CommonTools],
  data() {
    return {
      username: "",
      password: "",
      isLoggingIn: false
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
      if (!this.username || !this.password) {
        alert("Please enter username and password")
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
            alert(data.message || "Wrong Password!")
          }
        })
        .catch((err) => {
          this.isLoggingIn = false
          console.log("Login error:", err)
          alert("Login failed. Please try again.")
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
