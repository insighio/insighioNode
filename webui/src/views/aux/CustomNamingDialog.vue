<template>
  <div v-if="internalIsOpen" class="modal-overlay naming-overlay" @keydown="onKeydown">
    <div
      ref="dialog"
      class="modal-container naming-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="naming-dialog-title"
      aria-describedby="naming-dialog-intro"
      tabindex="-1"
    >
      <div class="modal-header naming-header">
        <h5 id="naming-dialog-title" class="modal-title">Custom Measurement Naming</h5>
        <button
          type="button"
          class="btn btn-link naming-close"
          aria-label="Close measurement naming"
          :disabled="isLoading"
          @click="requestClose"
        >
          <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" focusable="false">
            <path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
          </svg>
        </button>
      </div>
      <div class="modal-body naming-body">
        <p id="naming-dialog-intro" class="naming-intro">
          Optionally give each measurement an alias or a different unit. Use <strong>Fetch values</strong> to read the
          current values from the device; this can take up to a minute.
        </p>
        <p id="naming-alias-hint" class="naming-hint">Aliases may contain only letters, numbers and - _ / .</p>

        <div v-if="isLoading" class="naming-loading">
          <div class="naming-loading-text">
            <span class="loading" aria-hidden="true"></span>
            <span role="status">Reading measurements from the device&hellip;</span>
            <span class="naming-elapsed" aria-hidden="true">{{ progressValue }}s</span>
          </div>
          <progress
            class="progress naming-progress"
            :value="progressValue"
            max="60"
            aria-label="Measurement reading progress, in seconds"
          ></progress>
        </div>

        <div v-if="!isLoading && measurements.length === 0" class="naming-empty">
          No measurements yet. Press <strong>Fetch values</strong> to read them from the device.
        </div>

        <fieldset v-if="measurements.length > 0" class="naming-fieldset" :disabled="isLoading">
          <legend class="sr-only">Measurement aliases and units</legend>
          <table class="table naming-table">
            <thead>
              <tr>
                <th scope="col">Measurement</th>
                <th scope="col">Alias</th>
                <th scope="col">Unit</th>
                <th scope="col">Value</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(measurement, index) in measurements" :key="measurement.name" class="naming-row">
                <th scope="row" class="naming-name">{{ measurement.name }}</th>
                <td class="naming-alias" data-label="Alias">
                  <input
                    :id="'naming-alias-' + index"
                    v-model="measurement.alias"
                    type="text"
                    class="form-input"
                    :class="{ 'is-error': hasAliasIssue(measurement) }"
                    :aria-label="`Alias for ${measurement.name}`"
                    :aria-invalid="hasAliasIssue(measurement) ? 'true' : 'false'"
                    :aria-describedby="hasAliasIssue(measurement) ? `alias-error-${index}` : 'naming-alias-hint'"
                    autocapitalize="off"
                    autocomplete="off"
                    spellcheck="false"
                    placeholder="Optional"
                  />
                  <p
                    v-if="hasAliasIssue(measurement)"
                    :id="`alias-error-${index}`"
                    class="form-input-hint naming-error"
                  >
                    Only letters, numbers and <span class="naming-nowrap">- _ / .</span>
                  </p>
                </td>
                <td class="naming-unit" data-label="Unit">
                  <select
                    :id="'naming-unit-' + index"
                    :value="measurement.unit ?? ''"
                    @change="measurement.unit = $event.target.value"
                    class="form-select"
                    :aria-label="`Unit for ${measurement.name}`"
                  >
                    <option v-if="isUnknownUnit(measurement.unit)" :value="measurement.unit">
                      {{ measurement.unit }}
                    </option>
                    <option v-for="unitObj in unitOptions" :key="unitObj.unit" :value="unitObj.unit">
                      {{ formatUnitOption(unitObj) }}
                    </option>
                  </select>
                </td>
                <td class="naming-value" data-label="Value">{{ formatValue(measurement.value) }}</td>
              </tr>
            </tbody>
          </table>
        </fieldset>
      </div>
      <div class="modal-footer naming-footer">
        <button
          ref="fetchButton"
          type="button"
          class="btn naming-fetch"
          :disabled="isLoading"
          @click="executeMeasurements"
        >
          {{ hasFetched ? "Refresh values" : "Fetch values" }}
        </button>
        <button type="button" class="btn btn-cancel naming-cancel" :disabled="isLoading" @click="requestClose">
          Cancel
        </button>
        <button
          v-if="isSaveButtonVisible"
          type="button"
          class="btn btn-primary naming-primary"
          :disabled="isLoading"
          @click="validateMyForm"
        >
          Save &amp; continue
        </button>
        <button v-else type="button" class="btn btn-primary naming-primary" :disabled="isLoading" @click="doSkip">
          Skip naming
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { showAlert } from "@/js/appAlert.js"
import { fetchInternal } from "@/js/utils"
import { getMapObject } from "@/js/unitHelper"

const VALID_ALIAS_RE = /^[a-zA-Z0-9_/.-]+$/
const FOCUSABLE = "button:not([disabled]), input:not([disabled]), select:not([disabled]), [href]"

export default {
  name: "CustomNamingDialog",
  props: {
    isOpen: {
      type: Boolean,
      required: false
    }
  },
  emits: ["update:isOpen", "save", "close"],
  data() {
    return {
      storedMapping: undefined,
      measurements: [],
      unitOptions: [],
      isSaveButtonVisible: false,
      isLoading: false,
      rawMeasurementsRetrieved: undefined,
      progressValue: 0,
      progressTimer: undefined,
      hasFetched: false,
      returnFocusTo: null
    }
  },
  computed: {
    internalIsOpen: {
      get() {
        return this.isOpen
      },
      set(val) {
        this.$emit("update:isOpen", val)
      }
    },
    knownUnits() {
      return new Set(this.unitOptions.map((unitObj) => unitObj.unit))
    }
  },
  watch: {
    isOpen: {
      immediate: true,
      handler(open) {
        if (open) {
          this.returnFocusTo = document.activeElement
          this.$nextTick(() => {
            if (this.measurements.length === 0) this.$refs.fetchButton?.focus()
            else this.$refs.dialog?.focus()
          })
        } else {
          const target = this.returnFocusTo
          this.returnFocusTo = null
          if (target?.isConnected && target.offsetParent !== null) this.$nextTick(() => target.focus())
        }
      }
    }
  },
  mounted() {
    this.initialize()
  },
  beforeUnmount() {
    clearInterval(this.progressTimer)
  },
  methods: {
    requestClose() {
      if (!this.isLoading) this.$emit("close")
    },
    onKeydown(event) {
      if (event.key === "Escape") {
        event.preventDefault()
        this.requestClose()
        return
      }
      if (event.key !== "Tab") return

      const focusable = Array.from(this.$refs.dialog?.querySelectorAll(FOCUSABLE) || [])
      if (focusable.length === 0) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && (document.activeElement === first || document.activeElement === this.$refs.dialog)) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    },
    hasAliasIssue(measurement) {
      const alias = measurement.alias?.trim()
      return !!alias && !VALID_ALIAS_RE.test(alias)
    },
    isUnknownUnit(unit) {
      return !!unit && !this.knownUnits.has(unit)
    },
    formatUnitOption(unitObj) {
      return unitObj.unit ? `${unitObj.label} (${unitObj.unit})` : "No unit"
    },
    formatValue(value) {
      return value === undefined || value === null || value === "" ? "\u2014" : value
    },
    loadCookie(name) {
      let obj = this.$storage.get(name)

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

      this.progressTimer = setInterval(() => {
        if (this.progressValue >= 60) {
          clearInterval(this.progressTimer)
          this.isLoading = false
        } else {
          this.progressValue += 1
        }
      }, 1000)
    },
    stopProgress() {
      this.isLoading = false
      this.progressValue = 0
      clearInterval(this.progressTimer)
    },
    executeMeasurements() {
      // Keep keyboard focus inside the dialog while its buttons are disabled.
      this.$refs.dialog?.focus()
      this.progressValue = 0
      this.isLoading = true

      var cookieKeys = this.$storage.keys()
      var configString = ""
      var config = {} // or []

      cookieKeys.forEach((key) => {
        let value = this.$storage.get(key)

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

      if (!configString) {
        this.stopProgress()
        showAlert("There is no configuration to send to the device yet.", { type: "warning" })
        return
      }

      fetchInternal("/save-config-temp", 30000, "POST", objToSend, "json")
        .then(() => {
          this.startProgress()
          fetchInternal("/device_measurements", 60000)
            .then((measurementNaming) => {
              this.stopProgress()
              this.addStaticValuesForNetwork(measurementNaming)
              console.log("measurements: ", measurementNaming)

              this.rawMeasurementsRetrieved = { ...measurementNaming }

              const currentEdits = {}
              this.measurements.forEach((m) => (currentEdits[m.name] = m))

              this.measurements = []
              Object.keys(measurementNaming).forEach((measurementName) => {
                const tmpObj = measurementNaming[measurementName]
                var measurement = {
                  name: measurementName,
                  alias: "",
                  unit: tmpObj.unit,
                  value: tmpObj.value
                }

                // Keep aliases typed before a refresh; fall back to the stored mapping.
                let storedInfo = currentEdits[measurementName] || this.storedMapping[measurementName]
                if (storedInfo) {
                  if (storedInfo.alias) measurement.alias = storedInfo.alias
                  if (storedInfo.unit) measurement.unit = storedInfo.unit
                }

                this.measurements.push(measurement)
              })
              this.measurements.sort((a, b) => a.name.localeCompare(b.name))

              this.isSaveButtonVisible = true
              this.hasFetched = true
              this.isLoading = false
            })
            .catch((err) => {
              this.stopProgress()
              console.log("error fetching measurements: ", err)
              showAlert(
                "Could not read the measurements from the device. Check the sensor connections and try again.",
                {
                  type: "error"
                }
              )
            })
        })
        .catch((err) => {
          this.stopProgress()
          console.log("error saving config: ", err)
          showAlert("Could not send the configuration to the device. Check the connection and try again.", {
            type: "error"
          })
        })
    },
    addStaticValuesForNetwork(obj) {
      var net = this.$storage.get("network")
      var netStats = this.$storage.get("meas-network-stat")

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

      if (this.$storage.get("meas-gps-enabled") === "True") {
        obj["gps_lat"] = {}
        obj["gps_lon"] = {}
        obj["gps_num_of_sat"] = {}
        obj["gps_hdop"] = {}
      }

      obj["reset_cause"] = {}
      obj["uptime"] = { unit: "ms" }
    },
    clearCookies() {
      this.$storage.remove("meas-name-mapping")
      this.$storage.remove("meas-name-ext-mapping")
    },

    storeData() {
      this.clearCookies()
      this.$storage.set("meas-name-ext-mapping", this.getAliasUnitPairs())
      this.$emit("save")
    },
    validateMyForm() {
      const invalid = this.measurements.filter((measurement) => this.hasAliasIssue(measurement))

      if (invalid.length > 0) {
        const errorMessage =
          "Aliases may contain only letters, numbers and - _ / . Please fix:\n" +
          invalid.map((measurement) => measurement.name).join("\n")
        showAlert(errorMessage, { type: "warning" }).then(() => {
          const index = this.measurements.indexOf(invalid[0])
          // Run after the alert has restored focus to the button that opened it.
          setTimeout(() => document.getElementById("naming-alias-" + index)?.focus())
        })
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
        if (measurement.alias?.trim() || measurement.unit) {
          let newConfigObj = {}

          const storedUnit =
            this.rawMeasurementsRetrieved && this.rawMeasurementsRetrieved[measurement.name]
              ? this.rawMeasurementsRetrieved[measurement.name].unit
              : undefined

          const alias = measurement.alias?.trim()
          if (alias) newConfigObj.alias = alias
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
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1rem;
  z-index: 1000;
}

.modal-container.naming-dialog {
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 1000px;
  max-height: 90vh;
  max-height: 90dvh;
  padding: 0;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.naming-dialog:focus {
  outline: none;
}

.modal-header.naming-header {
  flex: none;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem 0.75rem 1.25rem;
  border-bottom: 1px solid var(--ui-border);
}

.naming-header .modal-title {
  margin: 0;
}

.btn.naming-close {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  padding: 0;
  border-radius: 50%;
  color: var(--ui-muted);
}

.btn.naming-close:hover,
.btn.naming-close:focus {
  color: var(--ui-accent);
  background: rgba(24, 110, 100, 0.08);
}

.modal-body.naming-body {
  flex: 1 1 auto;
  min-height: 0;
  max-height: none;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 1rem 1.25rem;
}

.naming-intro {
  margin: 0 0 0.35rem;
}

.naming-hint {
  margin: 0 0 1rem;
  color: var(--ui-muted);
  font-size: 0.75rem;
}

.naming-loading {
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  border: 1px solid var(--ui-border);
  border-radius: 8px;
  background: #f7fafb;
}

.naming-loading-text {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
  color: var(--ui-muted);
}

.naming-elapsed {
  margin-left: auto;
  font-variant-numeric: tabular-nums;
}

.naming-loading-text .loading {
  width: 1rem;
  height: 1rem;
}

.progress.naming-progress {
  width: 100%;
  accent-color: var(--ui-accent);
}

.progress.naming-progress::-webkit-progress-value {
  background: var(--ui-accent);
}

.progress.naming-progress::-moz-progress-bar {
  background: var(--ui-accent);
}

.naming-empty {
  padding: 2rem 1rem;
  border: 1px dashed var(--ui-border);
  border-radius: 8px;
  color: var(--ui-muted);
  text-align: center;
}

.naming-fieldset {
  margin: 0;
  padding: 0;
  border: 0;
  min-width: 0;
}

.naming-fieldset:disabled {
  opacity: 0.6;
}

.naming-table th,
.naming-table td {
  vertical-align: top;
}

.naming-table .naming-name {
  padding-top: 1.1rem;
  border-bottom-width: 1px;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.naming-table .naming-value {
  padding-top: 1.1rem;
  white-space: nowrap;
  color: var(--ui-muted);
}

.naming-table tbody tr:nth-child(odd) {
  background: #f7fafb;
}

.naming-nowrap {
  white-space: nowrap;
}

.naming-error {
  margin: 0.25rem 0 0;
  color: #c62828;
}

.modal-footer.naming-footer {
  flex: none;
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  border-top: 1px solid var(--ui-border);
}

.naming-footer .naming-fetch {
  margin-right: auto;
}

@media (max-width: 600px) {
  .modal-overlay {
    padding: 0;
    align-items: stretch;
  }

  .modal-container.naming-dialog {
    max-width: none;
    height: 100vh;
    height: 100dvh;
    max-height: none;
    border-radius: 0;
  }

  .modal-header.naming-header {
    padding: 0.5rem 0.5rem 0.5rem 1rem;
  }

  .modal-body.naming-body {
    padding: 1rem;
  }

  .naming-table thead {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip-path: inset(50%);
  }

  .naming-table,
  .naming-table tbody {
    display: block;
  }

  .naming-table tbody tr.naming-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 0.5rem 0.75rem;
    margin-bottom: 0.75rem;
    padding: 0.75rem;
    border: 1px solid var(--ui-border);
    border-radius: 8px;
    background: white;
  }

  .naming-table .naming-row > th,
  .naming-table .naming-row > td {
    display: block;
    padding: 0;
    border: 0;
  }

  .naming-table .naming-name,
  .naming-table .naming-value {
    padding-top: 0;
  }

  .naming-table .naming-alias,
  .naming-table .naming-unit {
    grid-column: 1 / -1;
  }

  .naming-table .naming-alias::before,
  .naming-table .naming-unit::before {
    content: attr(data-label);
    display: block;
    margin-bottom: 0.2rem;
    color: var(--ui-muted);
    font-size: 0.7rem;
    font-weight: 600;
  }

  .naming-table .naming-value {
    grid-row: 1;
    grid-column: 2;
    text-align: right;
  }

  .modal-footer.naming-footer {
    display: grid;
    grid-template-columns: 1fr 1fr;
    padding: 0.75rem 1rem calc(0.75rem + env(safe-area-inset-bottom, 0px));
  }

  .naming-footer .btn {
    width: 100%;
    margin: 0;
  }

  .naming-footer .naming-primary {
    grid-column: 1 / -1;
    grid-row: 1;
  }
}
</style>
