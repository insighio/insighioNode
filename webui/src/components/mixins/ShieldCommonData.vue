<script>
export default {
  data() {
    return {
      shieldNamePerTab: {
        "shield-accel-options": "accel",
        "shield-advind-options": "advind",
        "shield-scale-options": "scale",
        "shield-dig-analog-options": "dig_analog"
      },

      tabNamePerShield: {
        accel: "shield-accel-options",
        ins_esp_gen_sdi12: "shield-advind-options",
        ins_esp_gen_1: "shield-scale-options",
        ins_gen_s3: "shield-dig-analog-options",
        advind: "shield-advind-options",
        scale: "shield-scale-options",
        dig_analog: "shield-dig-analog-options"
      },

      i2cOptions: [
        { value: "disabled", label: "disabled" },
        { value: "tsl2561", label: "tsl2561 - luminosity" },
        { value: "sht20", label: "sht20 - temperature / humidity" },
        { value: "sht40", label: "sht40 - temperature / humidity" },
        { value: "si7021", label: "si7021 - temperature / humidity" },
        { value: "scd30", label: "scd30 - C02 / temperature / humidity" },
        { value: "bme680", label: "bme680 - gap / temperature / humidity" },
        { value: "sunrise", label: "sunrise - CO2 / temperature" },
        { value: "scd4x", label: "scd4x - CO2 / temperature / humidity" },
        { value: "sgx7ox", label: "sgx7ox - industrial oxygen sensor " }
      ],

      adcOptions: [
        { value: "disabled", label: "disabled" },
        { value: "dht11", label: "dht11 - temperature / humidity (digital)" },
        { value: "dht22", label: "dht22 - temperature / humidity (digital)" },
        { value: "ds18x20", label: "ds18x20 - temperature (OneWire)" },
        { value: "analog", label: "generic analog" }
      ]
    }
  }
}
</script>
