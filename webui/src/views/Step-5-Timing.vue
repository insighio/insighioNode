<template>
  <div class="form-group">
    <div class="text-center">Timing</div>
    <br />
    <ul class="tab tab-block">
      <li class="tab-item active" @click="timingChanged(event, 'periodic')">
        <a class="pointer">Periodic</a>
      </li>
      <li class="tab-item" @click="timingChanged(event, 'scheduled')">
        <a class="pointer">Time Scheduled</a>
      </li>
    </ul>
    <div id="periodic" class="tabcontent" style="display: block">
      <br />
      <br />
      <div class="columns flex-centered">
        <SInput
          label="Sleep Period (s)"
          v-model:value="timing_period"
          @update:value="timing_period = $event"
          @change="updateEstimatedTime()"
        />
        <br />
        <br />
        <SSwitch
          label="Light sleep ON"
          v-model:value="timing_light_sleep_on"
          @update:value="timing_light_sleep_on = $event"
        />

        <SSwitch
          label="Light sleep network active"
          v-model:value="timing_light_sleep_network_active"
          @update:value="timing_light_sleep_network_active = $event"
        />

        <SSwitch
          label="Light sleep deactivate on battery"
          v-model:value="timing_light_sleep_deactivate_on_battery"
          @update:value="timing_light_sleep_deactivate_on_battery = $event"
        />
      </div>
      <div class="form-group columns">
        <div class="col-1 col-mr-auto"></div>
        <div class="col-3 col-sm-12">
          <label class="form-label" for="measurements">Estimated Upload Period</label>
        </div>
        <div class="col-3 col-sm-12">
          <span> {{ timing_period }} </span> s <i class="icon icon-arrow-right"></i> <span>{{ timing_proc_h }}</span
          >:<span>{{ timing_proc_s }}</span>
          h
        </div>
        <div class="column col-5 col-mr-auto"></div>
      </div>
    </div>
    <div id="scheduled" class="tabcontent" style="display: none">
      <br />
      <br />
      Run two times in a day, at the timestamps defined below:
      <br />
      <br />
      <div class="columns flex-centered">
        <div class="col-1 col-sm-12">
          <label class="form-label" for="input-scheduled-time-a">A:</label>
        </div>
        <div class="col-3 col-sm-12">
          <input type="time" id="input-scheduled-time-a" name="appt" value="05:30" />
        </div>
        <div class="col-1 col-sm-12">
          <label class="form-label" for="input-scheduled-time-b">B:</label>
        </div>
        <div class="col-3 col-sm-12">
          <input type="time" id="input-scheduled-time-b" name="appt" value="21:30" />
        </div>
        <div class="column col-6 col-mr-auto"></div>
      </div>
    </div>
    <div>
      <br />
      <hr />
      <div class="columns flex-centered">
        <div class="columns col-12">
          <SSwitch
            label="Batch Upload"
            v-model:value="timing_batch_enabled"
            @update:value="timing_batch_enabled = $event"
          />
        </div>
        <div class="col-12" v-show="timing_batch_enabled">
          <br />
          <div class="form-group columns">
            <div class="col-1 col-mr-auto"></div>
            <SInput
              label="Message Buffer Size"
              v-model:value="timing_batch_upload_buffer_size"
              @update:value="bufferSizeUpdated($event)"
              :tooltip="batchTooltip"
              :colsLabel="3"
              :colsInput="3"
            />
            <div class="column col-5 col-mr-auto"></div>
          </div>
        </div>
      </div>
      <br />
      <br />
    </div>
    <WebuiFooter @savePressed="validateMyForm" @backPressed="requestGoBack" />
  </div>
</template>

<script>
import CommonTools from "@/components/mixins/CommonTools.vue"
import SSwitch from "@/components/SSwitch.vue"
import SInput from "@/components/SInput.vue"
import WebuiFooter from "@/components/WebuiFooter.vue"

export default {
  name: "Step5Timing",
  mixins: [CommonTools],
  components: { SSwitch, SInput, WebuiFooter },
  data() {
    return {
      // Add your component data here
      timing_light_sleep_on: false,
      timing_light_sleep_network_active: false,
      timing_light_sleep_deactivate_on_battery: false,
      timing_batch_upload_enable: false,
      timing_batch_upload_buffer_size: 1,
      timing_batch_enabled: false,
      timing_period: 300,
      timing_scheduled_time_a: "None",
      timing_scheduled_time_b: "None",
      timing_proc_h: 0,
      timing_proc_s: 0,
      batchTooltip:
        "Defines the number of measurements that\nshould be executed before the device\nconnects to the network and upload\nConnection period:\n   Sleep Period * Buffer Size"
    }
  },
  computed: {
    // Add your computed properties here
  },
  mounted() {
    // Add your mounted logic here
  },
  methods: {
    secondsToStringTime(seconds) {
      var hours = Math.floor(seconds / 3600)
      var minutes = (seconds % 3600) / 60

      return `${hours < 10 ? "0" : ""}${hours}:${minutes < 10 ? "0" : ""}${minutes}`
    },
    initializeValues() {
      this.timing_batch_upload_buffer_size = this.getValueWithDefaults(this.$cookies.get("batch-upload-buffer-size"), 1)
      let timeA = this.$cookies.get("scheduled-time-a")
      let timeB = this.$cookies.get("scheduled-time-b")

      if (timeA && timeB) {
        this.timingChanged(undefined, "scheduled")

        this.timing_scheduled_time_a = this.secondsToStringTime(timeA)
        this.timing_scheduled_time_b = this.secondsToStringTime(timeB)
      } else this.timingChanged(undefined, "periodic")

      this.timing_period = this.getValueWithDefaults(this.$cookies.get("period"), 300)
      this.timing_batch_enabled = this.timing_batch_upload_buffer_size && this.timing_batch_upload_buffer_size > 1

      this.timing_light_sleep_on = this.strToJSValue(this.$cookies.get("light-sleep-on"), false)
      this.timing_light_sleep_network_active = this.strToJSValue(this.$cookies.get("light-sleep-network-active"), false)
      this.timing_light_sleep_deactivate_on_battery = this.strToJSValue(
        this.$cookies.get("light-sleep-deactivate-on-battery"),
        false
      )

      //backward compatibility
      if (this.$cookies.get("always-on-period") !== undefined)
        this.timing_period = this.getValueWithDefaults(this.$cookies.get("period"), 300)

      if (this.$cookies.get("always-on-connection") !== undefined)
        this.timing_light_sleep_on = this.strToJSValue(this.$cookies.get("light-sleep-on"), false)

      if (this.$cookies.get("force-always-on-connection") !== undefined)
        this.this.timing_light_sleep_deactivate_on_battery = strToJSValue(
          this.$cookies.get("force-always-on-connection"),
          false
        )

      checkboxStatusChanged("ins-batch-upload")
      updateEstimatedTime()
      detectBoardChange(enableNavigationButtons)
    },
    bufferSizeUpdated(evt) {
      this.timing_batch_upload_buffer_size = evt
      this.updateEstimatedTime()
    },
    clearCookies() {
      this.$cookies.remove("period")
      this.$cookies.remove("batch-upload-buffer-size")
      this.$cookies.remove("scheduled-time-a")
      this.$cookies.remove("scheduled-time-b")
      this.$cookies.remove("always-on-connection")
      this.$cookies.remove("force-always-on-connection")
      this.$cookies.remove("always-on-period")

      this.$cookies.remove("light-sleep-on")
      this.$cookies.remove("light-sleep-network-active")
      this.$cookies.remove("light-sleep-deactivate-on-battery")
    },
    stringTimeToSeconds(timeStr) {
      var timeElements = timeStr.split(":")
      if (timeElements.length !== 2) return -1

      var timeSec = parseInt(timeElements[0]) * 3600 + parseInt(timeElements[1]) * 60
      console.log(timeStr + " to " + timeSec)
      return timeSec
    },
    storeData() {
      disableNavigationButtons()
      clearCookies()

      if (elementIsVisible("periodic")) {
        this.$cookies.set("period", document.getElementById("input-period").value)
        // this.$cookies.set('always-on-period', document.getElementById('input-always-on-period').value)
        // this.$cookies.set('always-on-connection', boolToPyStr('input-ins-always-on'))
        // this.$cookies.set('force-always-on-connection', boolToPyStr('input-ins-force-always-on'))
        this.$cookies.set("scheduled-time-a", "None")
        this.$cookies.set("scheduled-time-b", "None")

        this.$cookies.set("light-sleep-on", boolToPyStr("input-light-sleep-on"))
        this.$cookies.set("light-sleep-network-active", boolToPyStr("input-light-sleep-network-active"))
        this.$cookies.set("light-sleep-deactivate-on-battery", boolToPyStr("input-light-sleep-deactivate-on-battery"))
      } else if (elementIsVisible("scheduled")) {
        this.$cookies.set("period", "None")
        this.$cookies.set(
          "scheduled-time-a",
          stringTimeToSeconds(document.getElementById("input-scheduled-time-a").value)
        )
        this.$cookies.set(
          "scheduled-time-b",
          stringTimeToSeconds(document.getElementById("input-scheduled-time-b").value)
        )
      }

      if (document.getElementById("input-ins-batch-upload-enable").checked)
        this.$cookies.set("batch-upload-buffer-size", document.getElementById("input-message-buffer-size").value)
      else this.$cookies.set("batch-upload-buffer-size", "1")

      redirectTo("step-7-verify.html")
      enableNavigationButtons()
    },
    timingChanged(evt, boardDivId) {
      var i, tabcontent, tablinks

      tabcontent = document.getElementsByClassName("tabcontent")

      for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none"
      }

      tablinks = document.getElementsByClassName("tab-item")
      for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "")
      }

      showElement(boardDivId, true)

      var enableBatchUploadDefault = boardDivId !== "scheduled"
      document.getElementById("input-ins-batch-upload-enable").checked = enableBatchUploadDefault
      checkboxStatusChanged("ins-batch-upload")

      document.getElementById("tab-" + boardDivId).className += " active"
    },
    validateMyForm() {
      storeData()
      return true
    },
    batchUploadSelected() {
      checkboxStatusChanged("ins-batch-upload")
    },
    updateEstimatedTime() {
      console.log("to update estimated time")

      var seconds = this.timing_period
      var batchsize = this.timing_batch_upload_buffer_size

      var periodSeconds = seconds
      if (this.timing_batch_enabled && batchsize) periodSeconds = seconds * batchsize

      this.timing_proc_h = Math.floor(periodSeconds / 3600)
        .toString()
        .padStart(2, "0")

      this.timing_proc_s = ((periodSeconds % 3600) / 60).toFixed(0).toString().padStart(2, "0")
    }
  }
}
</script>

<style scoped>
.network {
  /* Add your component styles here */
}
</style>
