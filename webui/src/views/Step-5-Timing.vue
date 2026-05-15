<template>
  <div class="panel-body">
    <br />
    <div class="text-center">Timing:</div>
    <br />
    <div class="container grid-lg">
      <div class="columns flex-centered">
        <div class="column col-xl-7 col-md-10 col-sm-12">
          <ul class="tab tab-block">
            <li :class="['tab-item', { active: timing_type === 'periodic' }]" @click="timingChanged('periodic')">
              <a class="pointer">Periodic</a>
            </li>
            <li :class="['tab-item', { active: timing_type === 'scheduled' }]" @click="timingChanged('scheduled')">
              <a class="pointer">Time Scheduled</a>
            </li>
          </ul>
          <div v-if="timing_type === 'periodic'" class="tabcontent">
            <br />
            <br />
            <div class="columns flex-centered">
              <SInput label="Sleep Period (s)" v-model:value="timing_period" @update:value="sleepPeriodUpdated" />
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
              <div class="column col-1 col-mr-auto"></div>
              <div class="column col-3 col-sm-12">
                <label class="form-label" for="measurements">Estimated Upload Period</label>
              </div>
              <div class="column col-3 col-sm-12">
                <span> {{ timing_period }} </span> s <i class="icon icon-arrow-right"></i>
                <span>{{ timing_proc_h }}</span
                >:<span>{{ timing_proc_s }}</span>
                h
              </div>
              <div class="column col-5 col-mr-auto"></div>
            </div>
          </div>
          <div v-if="timing_type === 'scheduled'" class="tabcontent">
            <br />
            <br />
            Run two times in a day, at the timestamps defined below:
            <br />
            <br />
            <div class="columns flex-centered">
              <div class="column col-1 col-sm-12">
                <label class="form-label" for="input-scheduled-time-a">A:</label>
              </div>
              <div class="column col-3 col-sm-12">
                <input type="time" name="appt" value="05:30" />
              </div>
              <div class="column col-1 col-sm-12">
                <label class="form-label" for="input-scheduled-time-b">B:</label>
              </div>
              <div class="column col-3 col-sm-12">
                <input type="time" name="appt" value="21:30" />
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
                  @update:value="batchUploadStatusChanged"
                />
              </div>
              <div class="column col-12" v-show="timing_batch_enabled">
                <br />
                <div class="columns">
                  <div class="column col-1 col-mr-auto"></div>
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
      </div>
    </div>
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
      timing_type: "periodic",
      timing_light_sleep_on: false,
      timing_light_sleep_network_active: false,
      timing_light_sleep_deactivate_on_battery: false,
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
  mounted() {
    // Add your mounted logic here
    this.initializeValues()
  },
  methods: {
    secondsToStringTime(seconds) {
      var hours = Math.floor(seconds / 3600)
      var minutes = (seconds % 3600) / 60

      return `${hours < 10 ? "0" : ""}${hours}:${minutes < 10 ? "0" : ""}${minutes}`
    },
    initializeValues() {
      this.timing_batch_upload_buffer_size = this.getValueWithDefaults(this.$storage.get("batch-upload-buffer-size"), 1)
      let timeA = this.strToJSValue(this.$storage.get("scheduled-time-a"))
      let timeB = this.strToJSValue(this.$storage.get("scheduled-time-b"))

      if (timeA && timeB) {
        this.timingChanged("scheduled")

        this.timing_scheduled_time_a = this.secondsToStringTime(timeA)
        this.timing_scheduled_time_b = this.secondsToStringTime(timeB)
      } else this.timingChanged("periodic")

      this.timing_period = this.getValueWithDefaults(this.$storage.get("period"), 300)
      this.timing_batch_enabled = this.timing_batch_upload_buffer_size && this.timing_batch_upload_buffer_size > 1

      this.timing_light_sleep_on = this.strToJSValue(this.$storage.get("light-sleep-on"), false)
      this.timing_light_sleep_network_active = this.strToJSValue(this.$storage.get("light-sleep-network-active"), false)
      this.timing_light_sleep_deactivate_on_battery = this.strToJSValue(
        this.$storage.get("light-sleep-deactivate-on-battery"),
        false
      )

      //backward compatibility
      if (this.$storage.get("always-on-period") !== undefined)
        this.timing_period = this.getValueWithDefaults(this.$storage.get("period"), 300)

      if (this.$storage.get("always-on-connection") !== undefined)
        this.timing_light_sleep_on = this.strToJSValue(this.$storage.get("light-sleep-on"), false)

      if (this.$storage.get("force-always-on-connection") !== undefined)
        this.timing_light_sleep_deactivate_on_battery = this.strToJSValue(
          this.$storage.get("force-always-on-connection"),
          false
        )

      this.updateEstimatedTime()
    },
    bufferSizeUpdated(evt) {
      this.timing_batch_upload_buffer_size = evt
      this.updateEstimatedTime()
    },
    clearCookies() {
      this.$storage.remove("period")
      this.$storage.remove("batch-upload-buffer-size")
      this.$storage.remove("scheduled-time-a")
      this.$storage.remove("scheduled-time-b")
      this.$storage.remove("always-on-connection")
      this.$storage.remove("force-always-on-connection")
      this.$storage.remove("always-on-period")

      this.$storage.remove("light-sleep-on")
      this.$storage.remove("light-sleep-network-active")
      this.$storage.remove("light-sleep-deactivate-on-battery")
    },
    stringTimeToSeconds(timeStr) {
      var timeElements = timeStr.split(":")
      if (timeElements.length !== 2) return -1

      var timeSec = parseInt(timeElements[0]) * 3600 + parseInt(timeElements[1]) * 60
      console.log(timeStr + " to " + timeSec)
      return timeSec
    },
    storeData() {
      this.clearCookies()

      if (this.timing_type === "periodic") {
        this.$storage.set("period", this.timing_period)
        this.$storage.set("scheduled-time-a", "None")
        this.$storage.set("scheduled-time-b", "None")

        this.$storage.set("light-sleep-on", this.boolToPyStr(this.timing_light_sleep_on))
        this.$storage.set("light-sleep-network-active", this.boolToPyStr(this.timing_light_sleep_network_active))
        this.$storage.set(
          "light-sleep-deactivate-on-battery",
          this.boolToPyStr(this.timing_light_sleep_deactivate_on_battery)
        )
      } else if (this.timing_type === "scheduled") {
        this.$storage.set("period", "None")
        this.$storage.set("scheduled-time-a", this.stringTimeToSeconds(this.timing_scheduled_time_a))
        this.$storage.set("scheduled-time-b", this.stringTimeToSeconds(this.timing_scheduled_time_b))
      }

      console.log("this.timing_batch_enabled: ", this.timing_batch_enabled)
      console.log("this.timing_batch_upload_buffer_size: ", this.timing_batch_upload_buffer_size)

      if (this.timing_batch_enabled && this.timing_batch_upload_buffer_size >= 1)
        this.$storage.set("batch-upload-buffer-size", this.timing_batch_upload_buffer_size)
      else this.$storage.set("batch-upload-buffer-size", "1")

      this.requestGoNext()
    },
    timingChanged(boardDivId) {
      console.log("timingChanged: ", boardDivId)
      this.timing_type = boardDivId
      this.timing_batch_enabled = boardDivId !== "scheduled"
    },
    validateMyForm() {
      this.storeData()
      return true
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
    },
    sleepPeriodUpdated(newSleepPeriod) {
      this.timing_period = newSleepPeriod
      this.updateEstimatedTime()
    },
    batchUploadStatusChanged(new_batch_upload_status) {
      this.timing_batch_enabled = new_batch_upload_status
      this.updateEstimatedTime()
    }
  }
}
</script>
