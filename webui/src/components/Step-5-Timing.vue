<template>
  <div class="form-group">
    <div class="text-center">Timing</div>
    <br />
    <ul class="tab tab-block">
      <li id="tab-periodic" class="tab-item active" @click="timingChanged(event, 'periodic')">
        <a class="pointer">Periodic</a>
      </li>
      <li id="tab-scheduled" class="tab-item" @click="timingChanged(event, 'scheduled')">
        <a class="pointer">Time Scheduled</a>
      </li>
    </ul>
    <div id="periodic" class="tabcontent" style="display: block">
      <br />
      <br />
      <div class="columns flex-centered">
        <div class="col-4 col-sm-12">
          <label class="form-label" for="input-example-cellular">Sleep Period (s)</label>
        </div>
        <div class="col-8 col-sm-12">
          <input
            class="form-input constr-field"
            type="number"
            @change="updateEstimatedTime()"
            v-model="timing_period"
          />
        </div>
        <br />
        <br />
        <div class="columns col-12" style="padding-right: 0px; padding-left: 0px">
          <div class="col-4 col-sm-12">
            <label class="form-label">Light sleep ON</label>
          </div>
          <div class="col-8 col-sm-12">
            <label class="form-switch">
              <input type="checkbox" v-model="timing_light_sleep_on" />
              <i class="form-icon"></i>
            </label>
          </div>
        </div>
        <div class="columns col-12" style="padding-right: 0px; padding-left: 0px">
          <div class="col-4 col-sm-12">
            <label class="form-label">Light sleep network active</label>
          </div>
          <div class="col-8 col-sm-12">
            <label class="form-switch">
              <input type="checkbox" v-model="timing_light_sleep_network_active" />
              <i class="form-icon"></i>
            </label>
          </div>
        </div>
        <div class="columns col-12" style="padding-right: 0px; padding-left: 0px">
          <div class="col-4 col-sm-12">
            <label class="form-label">Light sleep deactivate on battery</label>
          </div>
          <div class="col-8 col-sm-12">
            <label class="form-switch">
              <input type="checkbox" v-model="timing_light_sleep_deactivate_on_battery" />
              <i class="form-icon"></i>
            </label>
          </div>
        </div>
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
          <div class="columns col-12" style="padding-right: 0px; padding-left: 0px">
            <div class="col-4 col-sm-12">
              <label class="form-label">Batch Upload</label>
            </div>
            <div class="col-8 col-sm-12">
              <label class="form-switch">
                <input type="checkbox" v-model="timing_batch_enabled" />
                <i class="form-icon"></i>
              </label>
            </div>
          </div>
        </div>
        <div class="col-12" v-show="timing_batch_enabled">
          <br />
          <div class="form-group columns">
            <div class="col-1 col-mr-auto"></div>
            <div class="col-3 col-sm-12">
              <label class="form-label" for="measurements"
                >Message Buffer Size
                <button
                  class="btn btn-link tooltip"
                  data-tooltip="Defines the number of measurements that&#xa;should be executed before the device&#xa;connects to the network and upload&#xa;Connection period:&#xa;   Sleep Period * Buffer Size"
                >
                  <i class="icon icon-flag"></i>
                </button>
              </label>
            </div>
            <div class="col-3 col-sm-12">
              <input
                class="form-input constr-field"
                type="number"
                @change="updateEstimatedTime()"
                id="input-message-buffer-size"
              />
            </div>
            <div class="column col-5 col-mr-auto"></div>
          </div>
        </div>
      </div>
      <br />
      <br />
    </div>
    <div class="column col-12">
      <button class="btn btn-primary float-right" @click="validateMyForm()" id="save-button" style="margin-left: 30px">
        Save
      </button>
      <button class="btn btn-primary float-right" type="button" id="back-button" @click="goBack()">Back</button>
    </div>
    <br />
    <br />
  </div>
</template>

<script>
export default {
  name: "Step5Timing",
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
      timing_proc_s: 0
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

      //backward compatibitily
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
        // this.$cookies.set('always-on-connection', boolElemToPyStr('input-ins-always-on'))
        // this.$cookies.set('force-always-on-connection', boolElemToPyStr('input-ins-force-always-on'))
        this.$cookies.set("scheduled-time-a", "None")
        this.$cookies.set("scheduled-time-b", "None")

        this.$cookies.set("light-sleep-on", boolElemToPyStr("input-light-sleep-on"))
        this.$cookies.set("light-sleep-network-active", boolElemToPyStr("input-light-sleep-network-active"))
        this.$cookies.set(
          "light-sleep-deactivate-on-battery",
          boolElemToPyStr("input-light-sleep-deactivate-on-battery")
        )
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
