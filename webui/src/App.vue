<template>
  <div id="app">
    <MainPage />
    <div class="watermark">Version: {{ appVersion }}</div>
  </div>
</template>

<script>
import MainPage from "@/views/MainPage.vue"
//const appVersion = import.meta.env.VITE_APP_VERSION || "unknown version"

export default {
  name: "App",
  components: {
    MainPage
  },
  data() {
    return {
      appVersion: "unknown version" // Placeholder for app version
    }
  },
  mounted() {
    this.getFirmwareVersion()
  },
  methods: {
    getFirmwareVersion() {
      fetch("/version")
        .then((response) => response.json())
        .then((data) => {
          this.appVersion = `${data.branch}:${data.commit}`
        })
        .catch((error) => {
          this.appVersion = "Error fetching version"
          console.error("Error fetching firmware version:", error)
        })
    }
  }
}
</script>

<style scoped>
header {
  line-height: 1.5;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
}

@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }

  .logo {
    margin: 0 2rem 0 0;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }
}

.watermark {
  position: fixed;
  bottom: 10px;
  right: 10px;
  font-size: 0.8rem;
  color: #888;
  opacity: 0.7;
}
</style>
