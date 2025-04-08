<template>
  <div v-if="internalIsOpen" class="modal-overlay">
    <div class="modal-container">
      <div class="modal-header">
        <h5 class="modal-title">Custom Measurement Naming</h5>
        <button class="btn btn-clear float-right" @click="$emit('close')"></button>
      </div>
      <div class="modal-body">
        <div v-if="isLoading" class="loading loading-lg"></div>
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
                <input type="text" v-model="measurement.alias" :id="'input-key-value-' + index" />
              </td>
              <td>
                <select v-model="measurement.unit" :id="'input-key-unit-' + index">
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
      <div class="toast">Accepted Characters: a-z, A-z, 0-9, -, _, /, .</div>
      <div class="modal-footer">
        <button class="btn btn-primary" @click="$emit('update')">Update</button>
        <button v-if="isSaveButtonVisible" class="btn btn-primary" @click="validateMyForm">Save</button>
        <button v-else class="btn btn-primary" @click="doSkip">Skip</button>
        <button class="btn btn-secondary" @click="$emit('close')">Close</button>
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
      measurements: [
        // { name: "Measurement 2", alias: "", unit: "unit2", value: 0 },
        // { name: "Measurement 1", alias: "", unit: "unit1", value: 0 }
      ],
      unitOptions: [],
      isSaveButtonVisible: false,
      isLoading: false
    }
  },
  mounted() {
    this.initialize()
  },
  methods: {
    loadCookie(name) {
      try {
        this.storedMapping = JSON.parse(this.$cookies.get(name))
        console.log("successfully parsed name", name)
        return this.storedMapping
      } catch (e) {
        console.log("failed parsing: ", name, ", error:", e)
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
          })

        this.storedMapping = editedMapping

        this.isSaveButtonVisible = true

        //populateTable(editedMapping)
      }
    },
    executeMeasurements() {
      this.isLoading = true

      var cookieKeys = this.$cookies.keys()
      var configString = ""
      var config = {} // or []

      cookieKeys.forEach((key) => {
        let value = this.$cookies.get(key)
        configString += key + "=" + value + "&"
        if (key == "wifi-ssid" || key == "wifi-pass" || key == "meas-keyvalue") {
          value = value.replaceAll("\\", "\\\\").replaceAll("'", "\\'")
        }
        config[key] = value
      })

      if (configString !== "") configString = configString.slice(0, -1)

      console.log("configString: ", configString)
      const objToSend = { queryParams: config }

      if (!configString) return

      fetch("/save-config-temp", {
        method: "POST",
        headers: {
          Accept: "application/json, text/plain, */*",
          "Content-Type": "application/json"
        },
        body: JSON.stringify(objToSend)
      })
        .then((res) => {
          fetchInternal("/device_measurements")
            .then((measurements) => {
              this.addStaticValuesForNetwork(measurements)
              console.log("measurements: ", measurements)
              this.measurements = measurements
              this.measurements.forEach((measurement) => {
                if (this.storedMapping[measurement.name]) {
                  measurement.alias = this.storedMapping[measurement.name].alias
                  measurement.unit = this.storedMapping[measurement.name].unit
                }
              })
              this.measurements.sort((a, b) => a.name.localeCompare(b.name))

              this.isSaveButtonVisible = true

              this.isLoading = false
            })
            .catch((err) => {
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

      if (net === "wifi" && netStats === "True") {
        obj["wifi_conn_duration"] = {}
        obj["wifi_scan_duration"] = {}
        obj["wifi_channel"] = {}
        obj["wifi_rssi"] = {}
      } else if (net === "cellular" && netStats === "True") {
        obj["cell_rssi"] = {}
        obj["cell_rsrp"] = {}
        obj["cell_rsrq"] = {}
        obj["cell_mcc"] = {}
        obj["cell_mnc"] = {}
        obj["cell_lac"] = {}
        obj["cell_ci"] = {}
        obj["cell_act_duration"] = {}
        obj["cell_att_duration"] = {}
        obj["cell_con_duration"] = {}
      }

      if (this.$cookies.get("meas-gps-enabled") === "True") {
        obj["gps_lat"] = {}
        obj["gps_lon"] = {}
        obj["gps_num_of_sat"] = {}
        obj["gps_hdop"] = {}
      }

      obj["reset_cause"] = {}
      obj["uptime"] = {}
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
      const validAliasRe = new RegExp("^[a-zA-Z-_/.]+$")
      var hasIssue = false

      this.measurements.forEach((measurement) => {
        if (measurement.alias && !validAliasRe.exec(measurement.alias.trim())) {
          measurement.hasIssue = true
          hasIssue = true
        }
      })

      if (hasIssue) {
        window.alert("Please use only accepted characters for alias: a-z, A-z, -, _, /, .")
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
        if (measurement.alias && measurement.unit) {
          aliasUnitPairs[measurement.name] = {
            alias: measurement.alias,
            unit: measurement.unit
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
