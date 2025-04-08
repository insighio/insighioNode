<template>
  <div class="panel-body">
    <br />
    <div class="empty">
      <div class="empty-icon">
        <i class="icon icon-2x icon-download"></i>
      </div>
      <p class="empty-title h5">Configuration Ready</p>
      <p class="empty-subtitle">
        The configuration is ready to be applied. By pressing the <span class="text-bold">Finish</span> button the
        device will reboot and start operating with the desired settings.
      </p>
      <div class="empty-action">
        <button class="btn btn-primary" style="margin-right: 10px" @click="requestGoBack()">Back</button>
        <button class="btn btn-primary" @click="requestGoNext()">Finish</button>
      </div>

      <br />
      <SDivider label="Key/Values" />
      <div class="columns" style="border-color: #c8c8c8">
        <div class="column col-6 col-sm-12">
          <table class="table">
            <tbody>
              <tr v-for="(config, index) in configToStoreOdd" :key="index">
                <td style="background-color: #e0e0e0">{{ config.key }}</td>
                <td>{{ config.value }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="column col-6 col-sm-12">
          <table class="table">
            <tbody>
              <tr v-for="(config, index) in configToStoreEven" :key="index">
                <td style="background-color: #e0e0e0">{{ config.key }}</td>
                <td>{{ config.value }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"
import SDivider from "@/components/SDivider.vue"

export default {
  name: "Step6Verify",
  mixins: [CommonTools],
  components: {
    SDivider
  },
  data() {
    return {
      // Add your component data here
      configToStore: [],
      configToStoreOdd: [],
      configToStoreEven: []
    }
  },
  computed: {
    // Add your computed properties here
  },
  mounted() {
    this.initializeValues()
  },
  methods: {
    // Add your component methods here
    initializeValues() {
      // Initialize values or perform any setup needed when the component is mounted

      this.$cookies.keys().forEach((key) => {
        this.configToStore.push({ key: key, value: this.$cookies.get(key) })
      })

      this.configToStoreOdd = this.configToStore.filter((_, index) => index % 2 === 0)
      this.configToStoreEven = this.configToStore.filter((_, index) => index % 2 !== 0)
    },
    storeAndReboot() {}
  }
}
</script>

<style scoped>
.network {
  /* Add your component styles here */
}
</style>
