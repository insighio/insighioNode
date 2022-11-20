import struct
import device_info
import logging
from micropython import const

# encoding protocol: https://docs.insigh.io/firmwareapi/lora/encodingprotocol/
# decoder: https://docs.insigh.io/firmwareapi/lora/decoder/


LOCATION_DEFAULT = const(0x00)
LOCATION_INTERNAL_BOARD = const(0x10)
LOCATION_INTERNAL_CPU = const(0x11)
LOCATION_I2C = const(0x20)
LOCATION_A_P1 = const(0x30)
LOCATION_A_P2 = const(0x31)
LOCATION_AD_P1 = const(0x40)
LOCATION_AD_P2 = const(0x41)
LOCATION_SDI12 = const(0x50)
LOCATION_MODEM = const(0x70)

TYPE_DEVICE_ID = const(0x01)
TYPE_RESET_CAUSE = const(0x02)
TYPE_UPTIME = const(0x03)
TYPE_MEM_ALLOC = const(0x04)
TYPE_MEM_FREE = const(0x05)
TYPE_CURRENT = const(0x07)
TYPE_VBAT = const(0x08)
TYPE_LIGHT_LUX = const(0x10)
TYPE_TEMPERATURE = const(0x11)
TYPE_HUMIDITY = const(0x12)
TYPE_CO2 = const(0x13)
TYPE_PRESSURE = const(0x14)
TYPE_GAS = const(0x15)
TYPE_VOLTAGE = const(0x16)
TYPE_VWC = const(0x17)
TYPE_REL_PERM = const(0x18)
TYPE_SOIL_EC = const(0x19)
TYPE_PORE_WATER_CONDUCT = const(0x20)
TYPE_SAP_FLOW = const(0x21)
TYPE_HEAT_VELOCITY = const(0x22)
TYPE_LOG_RATIO = const(0x23)
TYPE_LORA_JOIN_DUR = const(0xC1)
TYPE_GENERIC = const(0xE0)


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
        elif loc_name == "tsl2561":
            return LOCATION_I2C + 0
        elif loc_name == "si7021":
            return LOCATION_I2C + 1
        elif loc_name == "scd30":
            return LOCATION_I2C + 2
        elif loc_name == "bme680":
            return LOCATION_I2C + 3
        elif len(parts) > 2:
            if position == "ap1":
                return LOCATION_A_P1
            if position == "ap2":
                return LOCATION_A_P2
            if position == "adp1":
                return LOCATION_AD_P1
            if position == "adp2":
                return LOCATION_AD_P2
            if position[0] >= '0' and position[0] <= '9':
                return LOCATION_SDI12 + int(position[0])

    logging.error("returning default location for key: " + key)
    return LOCATION_DEFAULT


def create_message(device_id, measurements):
    logging.info("Device ID in readable form: {}".format(device_id))
    (_DEVICE_ID, _LORA_MAC) = device_info.get_device_id()

    binary_data = _LORA_MAC  # is it needed?

    import ubinascii

    # 'B' -> unsigned char -> 1 byte
    # 'H' -> unsigned short -> 2 bytes
    # 'h' -> short -> 2 bytes
    # 'I' -> unsigned int -> 4 bytes
    # 'i' -> int -> 4 bytes
    try:
        for key in sorted(measurements.keys()):
            logging.debug("Processing [{}]={}".format(key, measurements[key]["value"]))
            value = measurements[key]["value"]
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
            logging.debug("key testung: " + key)
            if key == "vbatt":
                binary_data += struct.pack('>BBH', TYPE_VBAT, LOCATION_INTERNAL_BOARD, value)
            elif key == "current":
                binary_data += struct.pack('>BBH', TYPE_CURRENT, LOCATION_INTERNAL_BOARD, value)
            elif key == "reset_cause":
                binary_data += struct.pack('>BBB', TYPE_RESET_CAUSE, LOCATION_INTERNAL_BOARD, value)
            elif key == "uptime":
                binary_data += struct.pack('>BBI', TYPE_UPTIME, LOCATION_INTERNAL_BOARD, value)
            elif key == "mem_alloc":
                binary_data += struct.pack('>BBI', TYPE_MEM_ALLOC, LOCATION_INTERNAL_BOARD, value)
            elif key == "mem_free":
                binary_data += struct.pack('>BBI', TYPE_MEM_FREE, LOCATION_INTERNAL_BOARD, value)
            elif key == "lora_join_duration":
                binary_data += struct.pack('>BBH', TYPE_LORA_JOIN_DUR, LOCATION_MODEM, value)
            # explicit cases should be added here
            # elif key == "new_explicit_value"
            #    do_stuff()
            elif key.endswith("_light"):
                binary_data += struct.pack('>BBH', TYPE_LIGHT_LUX, get_location_by_key(key), value)
            elif key.endswith("_temp"):
                binary_data += struct.pack('>BBh', TYPE_TEMPERATURE, get_location_by_key(key), round(value * 100))
            elif key.endswith("_humidity"):
                binary_data += struct.pack('>BBH', TYPE_HUMIDITY, get_location_by_key(key), round(value * 100))
            elif key.endswith("_co2"):
                binary_data += struct.pack('>BBH', TYPE_CO2, get_location_by_key(key), round(value * 100))
            elif key.endswith("_pressure"):
                binary_data += struct.pack('>BBi', TYPE_PRESSURE, get_location_by_key(key), round(value * 100))
            elif key.endswith("_gas"):
                binary_data += struct.pack('>BBH', TYPE_GAS, get_location_by_key(key), round(value * 100))
            elif key.endswith("_volt"):
                binary_data += struct.pack('>BBH', TYPE_VOLTAGE, get_location_by_key(key), value)
            elif key.endswith("_vwc"):
                binary_data += struct.pack('>BBH', TYPE_VWC, get_location_by_key(key), round(value * 100))
            elif key.endswith("_rel_perm"):
                binary_data += struct.pack('>BBH', TYPE_REL_PERM, get_location_by_key(key), round(value * 100))
            elif key.endswith("_soil_ec"):
                binary_data += struct.pack('>BBH', TYPE_SOIL_EC, get_location_by_key(key), round(value * 100))
            elif key.endswith("_pore_water_ec"):
                binary_data += struct.pack('>BBH', TYPE_GAS, get_location_by_key(key), round(value * 100))
            elif key.endswith("_sap_flow"):
                binary_data += struct.pack('>BBH', TYPE_SAP_FLOW, get_location_by_key(key), round(value * 100))
            elif key.endswith("_hv_outer") or key.endswith("_hv_inner"):
                binary_data += struct.pack('>BBH', TYPE_HEAT_VELOCITY, get_location_by_key(key), round(value * 100))
            elif key.endswith("_log_rt_a_outer") or key.endswith("_log_rt_a_inner"):
                binary_data += struct.pack('>BBI', TYPE_LOG_RATIO, get_location_by_key(key), round(value * 100000))
            elif "gen_" in key:
                keyParts = key.split("_")
                index = 0
                if len(keyParts) == 3:
                    try:
                        index = int(keyParts[2])
                    except Exception as e:
                        pass
                binary_data += struct.pack('>BBi', TYPE_GENERIC | index, get_location_by_key(key), round(value * 100))
            else:
                logging.error("Unregistered measurement: key: " + str(key) + ", value: " + str(value))
            logging.info("message: size[{}], data:[{}]".format(len(binary_data), ubinascii.hexlify(binary_data).decode('utf-8')))
    except:
        return ''

    return binary_data
