<template>
  <div v-if="internalIsOpen" class="modal-overlay">
    <div class="modal-container">
      <div class="modal-header">
        <h5 class="modal-title">Custom Measurement Naming</h5>
        <button class="btn btn-clear float-right" @click="$emit('close')"></button>
      </div>
      <div class="modal-body">
        <div v-if="isLoading" class="empty-subtitle">
          <div class="loading loading-lg"></div>
          <progress class="progress" :value="progressValue" max="60" style="margin: auto; width: 100%"></progress>
        </div>

        <table class="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Alias</th>
              <th>Unit</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(measurement, index) in measurements"
              :key="index"
              :class="[{ active: index % 2 === 0 }, 'table-row']"
            >
              <td>
                <input
                  type="text"
                  :value="measurement.name"
                  readonly
                  style="border-width: 0px; border: none; box-shadow: none"
                />
              </td>
              <td>
                <input type="text" v-model="measurement.alias" :id="'value-' + index" />
              </td>
              <td>
                <select v-model="measurement.unit" :id="'unit-' + index">
                  <option v-for="unitObj in unitOptions" :key="unitObj.unit" :value="unitObj.unit">
                    {{ unitObj.label }}
                  </option>
                </select>
              </td>
              <td>{{ measurement.value }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="toast">Accepted Characters: a-z, A-Z, 0-9, -, _, /, .</div>
      <div class="modal-footer">
        <div class="float-left"><button class="btn btn-primary" @click="executeMeasurements">Fetch</button></div>
        <div class="float-right">
          <button v-if="isSaveButtonVisible" class="btn btn-primary" @click="validateMyForm">Save</button>
          <button v-else class="btn btn-primary" @click="doSkip">Next</button>
        </div>
        <div class="float-right">
          <button class="btn btn-secondary" @click="$emit('close')">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { fetchInternal } from "@/js/utils"
import { getMapObject } from "@/js/unitHelper"

export default {
  name: "CustomNamingDialog",
  props: {
    isOpen: {
      type: Boolean,
      required: false
    }
  },
  emits: ["update:isOpen", "save"],
  computed: {
    internalIsOpen: {
      get() {
        return this.isOpen
      },
      set(val) {
        this.$emit("update:isOpen", val)
      }
    }
  },
  data() {
    return {
      storedMapping: undefined,
      measurements: [],
      unitOptions: [],
      isSaveButtonVisible: false,
      isLoading: false,
      rawMeasurementsRetrieved: undefined,
      progressValue: 0
    }
  },
  mounted() {
    this.initialize()
  },
  methods: {
    loadCookie(name) {
      let obj = this.$cookies.get(name)

      if (typeof obj === "string") {
        try {
          this.storedMapping = JSON.parse(obj)
          console.log("successfully parsed name", name)
          return this.storedMapping
        } catch (e) {
          console.log("failed parsing: ", name, ", error:", e)
        }
      } else if (typeof obj === "object") {
        this.storedMapping = obj
        console.log("successfully loaded name", name)
        return this.storedMapping
      }
      return undefined
    },
    initialize() {
      this.unitOptions = getMapObject()
      console.log("this.unitOptions: ", this.unitOptions)

      if (!this.loadCookie("meas-name-ext-mapping") && !this.loadCookie("meas-name-mapping")) {
        this.storedMapping = {}
      } else {
        var editedMapping = {}

        Object.keys(this.storedMapping)
          .sort()
          .forEach((measurement_name) => {
            var new_obj = {
              alias: "",
              unit: ""
            }

            if (this.storedMapping[measurement_name]) {
              if (typeof this.storedMapping[measurement_name] === "string")
                new_obj.alias = this.storedMapping[measurement_name]
              else new_obj.alias = this.storedMapping[measurement_name].alias
            }

            if (this.storedMapping[measurement_name] && typeof this.storedMapping[measurement_name] !== "string") {
              new_obj.unit = this.storedMapping[measurement_name].unit
              new_obj.unitUpdated = true
            }

            editedMapping[measurement_name] = { ...new_obj }

            this.measurements.push({
              name: measurement_name,
              alias: new_obj.alias,
              unit: new_obj.unit,
              value: undefined
            })
          })

        this.storedMapping = editedMapping

        this.isSaveButtonVisible = true

        //populateTable(editedMapping)
      }
    },
    startProgress() {
      this.progressValue = 0

      const interval = setInterval(() => {
        if (this.progressValue >= 60) {
          clearInterval(interval)
          this.isLoading = false
        } else {
          this.progressValue += 1
        }
      }, 1000)
    },
    stopProgress() {
      this.isLoading = false
      this.progressValue = 0
    },
    executeMeasurements() {
      this.progressValue = 0
      this.isLoading = true

      var cookieKeys = this.$cookies.keys()
      var configString = ""
      var config = {} // or []

      cookieKeys.forEach((key) => {
        let value = this.$cookies.get(key)

        if (typeof value === "object") {
          value = JSON.stringify(value)
        }

        if (value === undefined || value === null || value === "null") return

        console.log("cookie: ", key, " value: ", value)
        configString += key + "=" + value + "&"

        if (
          key === "wifi-ssid" ||
          key === "wifi-pass" ||
          key === "meas-name-mapping" ||
          key === "meas-name-ext-mapping" ||
          key === "meas-keyvalue" ||
          key === "meas-sdi12" ||
          key === "meas-modbus" ||
          key === "meas-adc" ||
          key === "meas-pulseCounter" ||
          key === "system-settings"
        ) {
          value = value.replaceAll("\\", "\\\\").replaceAll("'", "\\'")
        }
        config[key] = value
      })

      if (configString !== "") configString = configString.slice(0, -1)

      console.log("configString: ", configString)
      const objToSend = { queryParams: config }

      if (!configString) return

      fetch("http://192.168.4.1" + "/save-config-temp", {
        method: "POST",
        headers: {
          Accept: "application/json, text/plain, */*",
          "Content-Type": "application/json"
        },
        body: JSON.stringify(objToSend)
      })
        .then((res) => {
          this.startProgress()
          fetchInternal("/device_measurements", 60000)
            .then((measurementNaming) => {
              this.stopProgress()
              this.addStaticValuesForNetwork(measurementNaming)
              console.log("measurements: ", measurementNaming)

              this.rawMeasurementsRetrieved = { ...measurementNaming }

              this.measurements = []
              Object.keys(measurementNaming).forEach((measurementName) => {
                const tmpObj = measurementNaming[measurementName]
                var measurement = {
                  name: measurementName,
                  alias: "",
                  unit: tmpObj.unit,
                  value: tmpObj.value
                }

                let storedInfo = this.storedMapping[measurementName]
                if (storedInfo) {
                  if (storedInfo.alias) measurement.alias = storedInfo.alias
                  if (storedInfo.unit) measurement.unit = storedInfo.unit
                }

                this.measurements.push(measurement)
              })
              this.measurements.sort((a, b) => a.name.localeCompare(b.name))

              this.isSaveButtonVisible = true
              this.isLoading = false
            })
            .catch((err) => {
              this.stopProgress()
              this.isLoading = false
              console.log("error fetching measurements: ", err)
            })
        })
        .catch((err) => {
          console.log("error saving config: ", err)
        })
    },
    addStaticValuesForNetwork(obj) {
      var net = this.$cookies.get("network")
      var netStats = this.$cookies.get("meas-network-stat")

      if (netStats === "True") {
        if (net === "wifi") {
          obj["wifi_conn_duration"] = { unit: "ms" }
          obj["wifi_scan_duration"] = { unit: "ms" }
          obj["wifi_channel"] = {}
          obj["wifi_rssi"] = { unit: "dBm" }
        } else if (net === "cellular") {
          obj["cell_rssi"] = { unit: "dBm" }
          obj["cell_rsrp"] = { unit: "dBm" }
          obj["cell_rsrq"] = { unit: "dBm" }
          obj["cell_mcc"] = {}
          obj["cell_mnc"] = {}
          obj["cell_lac"] = {}
          obj["cell_ci"] = {}
          obj["cell_act_duration"] = { unit: "ms" }
          obj["cell_att_duration"] = { unit: "ms" }
          obj["cell_con_duration"] = { unit: "ms" }
        }
      }

      if (this.$cookies.get("meas-gps-enabled") === "True") {
        obj["gps_lat"] = {}
        obj["gps_lon"] = {}
        obj["gps_num_of_sat"] = {}
        obj["gps_hdop"] = {}
      }

      obj["reset_cause"] = {}
      obj["uptime"] = { unit: "ms" }
    },
    clearCookies() {
      this.$cookies.remove("meas-name-mapping")
      this.$cookies.remove("meas-name-ext-mapping")
    },

    storeData() {
      this.clearCookies()
      this.$cookies.set("meas-name-ext-mapping", this.getAliasUnitPairs())
      this.$emit("save")
    },
    validateMyForm() {
      const validAliasRe = new RegExp("^[a-zA-Z0-9\-_\/\.]+$")
      var hasIssue = false

      this.measurements.forEach((measurement) => {
        if (measurement.alias && !validAliasRe.exec(measurement.alias.trim())) {
          measurement.hasIssue = true
          hasIssue = true
        }
      })

      if (hasIssue) {
        let errorMessage = "Please use only accepted characters for alias: a-z, A-Z, -, _, /, ."
        this.measurements.forEach((measurement) => {
          if (measurement.hasIssue) {
            errorMessage += "\n" + measurement.name
          }
        })
        window.alert(errorMessage)
        return false
      }

      this.storeData()
      return true
    },
    doSkip() {
      this.$emit("save")
    },
    getAliasUnitPairs() {
      const aliasUnitPairs = {}

      this.measurements.forEach((measurement) => {
        if (measurement.alias || measurement.unit) {
          let newConfigObj = {}

          const storedUnit =
            this.rawMeasurementsRetrieved && this.rawMeasurementsRetrieved[measurement.name]
              ? this.rawMeasurementsRetrieved[measurement.name].unit
              : undefined

          if (measurement.alias) newConfigObj.alias = measurement.alias
          if (measurement.unit !== storedUnit) newConfigObj.unit = measurement.unit

          //new config
          if (Object.keys(newConfigObj).length > 0) {
            aliasUnitPairs[measurement.name] = newConfigObj
          }
        }
      })
      return aliasUnitPairs
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-container {
  background: white;
  border-radius: 5px;
  width: 90%;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  max-width: 1000px;
}

.modal-header {
  padding: 1rem;
  border-bottom: 1px solid #e5e5e5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-body {
  padding: 1rem;
}

.modal-footer {
  padding: 1rem;
  border-top: 1px solid #e5e5e5;
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}
</style>
