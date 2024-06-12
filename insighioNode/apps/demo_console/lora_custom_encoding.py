import struct
import device_info
import logging

# encoding protocol: https://docs.insigh.io/firmwareapi/lora/encodingprotocol/
# decoder: https://docs.insigh.io/firmwareapi/lora/decoder/


LOCATION_DEFAULT = 0x00
LOCATION_INTERNAL_BOARD = 0x10
LOCATION_INTERNAL_CPU = 0x11
LOCATION_I2C = 0x20
LOCATION_A_P1 = 0x30
LOCATION_A_P2 = 0x31
LOCATION_AD_P1 = 0x40
LOCATION_AD_P2 = 0x41
LOCATION_SDI12 = 0x50
LOCATION_4_20 = 0x60
LOCATION_MODEM = 0x70
LOCATION_GPS = 0x71
LOCATION_WEATHER_STATION = 0x80
LOCATION_RAIN_GAUGE = 0x81
LOCATION_SOLAR_SENSOR = 0x82
LOCATION_PULSE_COUNTER = 0x83
LOCATION_WEATHER_STATION_WIND = 0x84

TYPE_DEVICE_ID = 0x01
TYPE_RESET_CAUSE = 0x02
TYPE_UPTIME = 0x03
TYPE_MEM_ALLOC = 0x04
TYPE_MEM_FREE = 0x05
TYPE_CURRENT = 0x07
TYPE_VBAT = 0x08
TYPE_LIGHT_LUX = 0x10
TYPE_TEMPERATURE_CEL = 0x11
TYPE_HUMIDITY = 0x12
TYPE_CO2 = 0x13
TYPE_PRESSURE = 0x14
TYPE_GAS = 0x15
TYPE_VOLTAGE = 0x16
TYPE_VWC = 0x17
TYPE_REL_PERM = 0x18
TYPE_SOIL_EC = 0x19
TYPE_MILLIMETER = 0x1A
TYPE_WATTS_PER_SQUARE_METER = 0x1B
TYPE_GRAMS_OF_WATER_VAPOUR_PER_CUBIC_METRE_OF_AIR = 0x1C
TYPE_ACTUAL_EVAPOTRANSPIRATION_MM = 0x1D
TYPE_LATENT_ENERGY_FLUX = 0x1E
TYPE_HEAT_FLUX = 0x1F
TYPE_PORE_WATER_CONDUCT = 0x20
TYPE_SAP_FLOW = 0x21
TYPE_HEAT_VELOCITY = 0x22
TYPE_LOG_RATIO = 0x23
TYPE_VAPOR_PRESSURE_DEFICIT = 0x24
TYPE_ATMOSPHERIC_PRESSURE = 0x25
TYPE_TEMPERATURE_FAH = 0x26
TYPE_DEVIATION = 0x27
TYPE_RADIATION = 0x28
TYPE_COUNT = 0x29
TYPE_HEIGHT = 0x2A
TYPE_PERIOD = 0x2B
TYPE_NOISE = 0x2C
TYPE_DIRECTION_DEG = 0x2D
TYPE_DIRECTION_ID = 0x2E
TYPE_SPEED = 0x2F
TYPE_FORMULA = 0x30
TYPE_LORA_JOIN_DUR = 0xC1
TYPE_GPS_HDOP = 0xD0
TYPE_GPS_LAT = 0xD1
TYPE_GPS_LON = 0xD2
TYPE_GENERIC = 0xE0


def get_location_by_key(key):
    if key:
        parts = key.split("_")

        if len(parts) < 2:
            logging.error("returning default location for key: [" + key + "]")
            return LOCATION_DEFAULT

        loc_name = parts[0]
        position = parts[1]

        if loc_name == "board":
            return LOCATION_INTERNAL_BOARD
        elif loc_name == "cpu":
            return LOCATION_INTERNAL_CPU
        elif loc_name == "pcnt":
            return LOCATION_PULSE_COUNTER
        elif loc_name == "rain":
            return LOCATION_RAIN_GAUGE
        elif loc_name == "solar":
            return LOCATION_SOLAR_SENSOR
        elif loc_name == "wth":
            if len(parts) > 2 and position == "wind":
                return LOCATION_WEATHER_STATION_WIND
            else:
                return LOCATION_WEATHER_STATION
        elif loc_name == "tsl2561":
            return LOCATION_I2C + 0
        elif loc_name == "si7021":
            return LOCATION_I2C + 1
        elif loc_name == "scd30":
            return LOCATION_I2C + 2
        elif loc_name == "bme680":
            return LOCATION_I2C + 3
        elif loc_name == "sht20":
            return LOCATION_I2C + 4
        elif loc_name == "sht40":
            return LOCATION_I2C + 5
        elif loc_name == "sunrise":
            return LOCATION_I2C + 6
        elif loc_name == "4-20" and position[0] >= "0" and position[0] <= "9":
            return LOCATION_4_20 + int(position[0])
        elif loc_name == "sdi12" and position[0] >= "0" and position[0] <= "9":
            return LOCATION_SDI12 + int(position[0])
        elif len(parts) > 2:
            if position == "ap1":
                return LOCATION_A_P1
            elif position == "ap2":
                return LOCATION_A_P2
            elif position == "adp1":
                return LOCATION_AD_P1
            elif position == "adp2":
                return LOCATION_AD_P2
            elif position[0] >= "0" and position[0] <= "9":
                return LOCATION_SDI12 + int(position[0])

    logging.error("returning default location for key: " + key)
    return LOCATION_DEFAULT


def create_message(device_id, measurements):
    logging.info("Device ID in readable form: {}".format(device_id))
    (_DEVICE_ID, _DEVICE_ID_BYTES) = device_info.get_device_id()

    binary_data = _DEVICE_ID_BYTES

    import ubinascii

    # 'B' -> unsigned char -> 1 byte
    # 'H' -> unsigned short -> 2 bytes
    # 'h' -> short -> 2 bytes
    # 'I' -> unsigned int -> 4 bytes
    # 'i' -> int -> 4 bytes
    try:
        for key in sorted(measurements.keys()):
            logging.debug("Processing [{}]={}".format(key, measurements[key]))
            try:
                value = measurements[key]["value"]
            except:
                value = measurements[key]
            keyparts = key.split("_")
            measurement_index = None
            if len(keyparts) > 1:
                try:
                    # check if value key has index value at the end of the name: ex. gen_vwc_1 instead of gen_vwc
                    index = int(keyparts[-1])
                    if index >= 0 and index <= 16:
                        measurement_index = index
                        key = "_".join(keyparts[0:-1])
                except:
                    pass
            logging.debug("key testing: " + key)
            if key == "vbatt":
                binary_data += struct.pack(">BBH", TYPE_VBAT, LOCATION_INTERNAL_BOARD, value)
            elif key == "reset_cause":
                binary_data += struct.pack(">BBB", TYPE_RESET_CAUSE, LOCATION_INTERNAL_BOARD, value)
            elif key == "uptime":
                binary_data += struct.pack(">BBI", TYPE_UPTIME, LOCATION_INTERNAL_BOARD, value)
            elif key == "mem_alloc":
                binary_data += struct.pack(">BBI", TYPE_MEM_ALLOC, LOCATION_INTERNAL_BOARD, value)
            elif key == "mem_free":
                binary_data += struct.pack(">BBI", TYPE_MEM_FREE, LOCATION_INTERNAL_BOARD, value)
            elif key == "lora_join_duration":
                binary_data += struct.pack(">BBH", TYPE_LORA_JOIN_DUR, LOCATION_MODEM, value)

            elif key == "gps_hdop":
                binary_data += struct.pack(">BBB", TYPE_GPS_HDOP, LOCATION_GPS, round(value * 10))
            elif key == "gps_lat":
                binary_data += struct.pack(">BBI", TYPE_GPS_LAT, LOCATION_GPS, round(value * 100000))
            elif key == "gps_lon":
                binary_data += struct.pack(">BBI", TYPE_GPS_LON, LOCATION_GPS, round(value * 100000))
            elif key == "gps_dur":
                binary_data += struct.pack(">BBI", TYPE_UPTIME, LOCATION_GPS, value)

            elif key.endswith("_deviation"):
                binary_data += struct.pack(">BBh", TYPE_DEVIATION, get_location_by_key(key), round(value * 100))
            elif key.endswith("_radiation"):
                binary_data += struct.pack(">BBH", TYPE_RADIATION, get_location_by_key(key), value)
            elif key.endswith("_count"):
                binary_data += struct.pack(">BBH", TYPE_COUNT, get_location_by_key(key), round(value * 10))
            elif key.endswith("_height"):
                binary_data += struct.pack(">BBH", TYPE_HEIGHT, get_location_by_key(key), round(value * 10))
            elif key.endswith("_period"):
                binary_data += struct.pack(">BBH", TYPE_PERIOD, get_location_by_key(key), round(value * 10))
            elif key.endswith("_noise"):
                binary_data += struct.pack(">BBH", TYPE_NOISE, get_location_by_key(key), round(value * 10))
            elif key.endswith("_d"):
                binary_data += struct.pack(">BBH", TYPE_DIRECTION_DEG, get_location_by_key(key), round(value * 10))
            elif key.endswith("_direction"):
                binary_data += struct.pack(">BBB", TYPE_DIRECTION_ID, get_location_by_key(key), value)
            elif key.endswith("_speed"):
                binary_data += struct.pack(">BBh", TYPE_SPEED, get_location_by_key(key), round(value * 100))

            # explicit cases should be added here
            # elif key == "new_explicit_value"
            #    do_stuff()
            elif key.endswith("_light"):
                binary_data += struct.pack(">BBH", TYPE_LIGHT_LUX, get_location_by_key(key), value)
            elif key.endswith("_temp"):
                binary_data += struct.pack(">BBh", TYPE_TEMPERATURE_CEL, get_location_by_key(key), round(value * 100))
            elif key.endswith("_humidity") or key.endswith("_hum"):
                binary_data += struct.pack(">BBH", TYPE_HUMIDITY, get_location_by_key(key), round(value * 100))
            elif key.endswith("_co2"):
                binary_data += struct.pack(">BBH", TYPE_CO2, get_location_by_key(key), round(value * 100))
            elif key.endswith("_pressure"):
                binary_data += struct.pack(">BBi", TYPE_PRESSURE, get_location_by_key(key), round(value * 100))
            elif key.endswith("_gas"):
                binary_data += struct.pack(">BBH", TYPE_GAS, get_location_by_key(key), round(value * 100))
            elif key.endswith("_volt"):
                binary_data += struct.pack(">BBH", TYPE_VOLTAGE, get_location_by_key(key), value)
            elif key.endswith("_vwc"):
                binary_data += struct.pack(">BBH", TYPE_VWC, get_location_by_key(key), round(value * 100))
            elif key.endswith("_rel_perm"):
                binary_data += struct.pack(">BBH", TYPE_REL_PERM, get_location_by_key(key), round(value * 100))
            elif key.endswith("_soil_ec"):
                binary_data += struct.pack(">BBH", TYPE_SOIL_EC, get_location_by_key(key), round(value * 100))
            elif key.endswith("_pore_water_ec"):
                binary_data += struct.pack(">BBH", TYPE_GAS, get_location_by_key(key), round(value * 100))
            elif key.endswith("_sap_flow"):
                binary_data += struct.pack(">BBH", TYPE_SAP_FLOW, get_location_by_key(key), round(value * 100))
            elif key.endswith("_hv_outer") or key.endswith("_hv_inner"):
                binary_data += struct.pack(">BBH", TYPE_HEAT_VELOCITY, get_location_by_key(key), round(value * 100))
            elif key.endswith("_log_rt_a_outer") or key.endswith("_log_rt_a_inner"):
                binary_data += struct.pack(">BBI", TYPE_LOG_RATIO, get_location_by_key(key), round(value * 100000))
            elif key.endswith("_current"):
                binary_data += struct.pack(">BBH", TYPE_CURRENT, get_location_by_key(key), round(value * 100))
            elif key.endswith("_formula"):
                binary_data += struct.pack(">BBI", TYPE_FORMULA, get_location_by_key(key), round(value * 100000))

            elif key.endswith("_et"):
                binary_data += struct.pack(">BBH", TYPE_ACTUAL_EVAPOTRANSPIRATION_MM, get_location_by_key(key), round(value * 1000))
            elif key.endswith("_le"):
                binary_data += struct.pack(">BBH", TYPE_LATENT_ENERGY_FLUX, get_location_by_key(key), round(value * 10))
            elif key.endswith("_h"):
                binary_data += struct.pack(">BBH", TYPE_HEAT_FLUX, get_location_by_key(key), round(value * 10))
            elif key.endswith("_vpd"):
                binary_data += struct.pack(">BBH", TYPE_VAPOR_PRESSURE_DEFICIT, get_location_by_key(key), round(value * 10))
            elif key.endswith("_pa"):
                binary_data += struct.pack(">BBH", TYPE_ATMOSPHERIC_PRESSURE, get_location_by_key(key), round(value * 10))
            elif key.endswith("_taf"):
                binary_data += struct.pack(">BBH", TYPE_TEMPERATURE_FAH, get_location_by_key(key), round(value * 100))
            elif key.endswith("_rh"):
                binary_data += struct.pack(">BBH", TYPE_HUMIDITY, get_location_by_key(key), round(value * 100))
            elif key.endswith("_seq"):
                binary_data += struct.pack(">BBH", TYPE_GENERIC, get_location_by_key(key), value)
            elif key.endswith("_diag"):
                binary_data += struct.pack(">BBH", TYPE_GENERIC | 0x01, get_location_by_key(key), value)

            else:
                index = measurement_index if measurement_index is not None else 0

                if type(value) == int or type(value) == float:
                    binary_data += struct.pack(">BBi", TYPE_GENERIC + index, get_location_by_key(key), round(value * 100))
                else:
                    logging.error("Unidentified or unaccepted measurement: key: {}, value: {}, type: {}".format(key, value, type(value)))
            logging.info("message: size[{}], data:[{}]".format(len(binary_data), ubinascii.hexlify(binary_data).decode("utf-8")))
    except Exception as e:
        logging.exception(e, "Error encoding lora message")
        return ""

    return binary_data
