<template>
  <div class="panel-body">
    <br />
    <hr />
    <br />
    <div class="container">
      <div class="columns flex-centered">
        <div class="column col-6 col-xl-8 col-md-10 col-sm-12">
          <div class="form-group">
            <label class="form-label" for="input-example-1">Username</label>
            <input class="form-input constr-field" type="text" placeholder="Username" v-model="username" />
            <label class="form-label" for="input-example-1">Password</label>
            <input class="form-input constr-field" type="password" placeholder="Password" v-model="password" />
            <br />
            <div class="flex-centered">
              <button class="btn btn-primary constr-field" @click="checkPassword()">Login</button>
            </div>
            <br />
            <br />
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

export default {
  name: "Step1Login",
  mixins: [CommonTools],
  data() {
    return {
      username: "",
      password: ""
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
      if (this.username === "admin" && this.password === "insighiodev") {
        this.clearAllCookies()
        this.$cookies.set("session", "true")
        this.requestGoNext()
        return true
      } else {
        alert("Wrong Password!")
        return false
      }
    },
    checkAlreadyLoggedIn() {
      if (this.$cookies.isKey("session")) {
        this.requestGoNext()
      }
    }
  }
}
</script>
