def device_info_get_device_id():
    return ("f412fac3b9c4", b"\xf4\x12\xfa\xc3\xb9\xc4")


import sys
import binascii
import struct
import re

module = type(sys)("device_info")
module.get_device_id = device_info_get_device_id
sys.modules["device_info"] = module

sys.modules["ubinascii"] = binascii
sys.modules["ure"] = re

# import sys
# module = type(sys)("my_module_name")
# module.submodule = type(sys)("my_submodule_name")
# module.submodule.something = something
# sys.modules["my_module_name"] = module
# sys.modules["my_module_name.my_submodule_name"] = module.submodule

from insighioNode.apps.demo_console import lora_custom_encoding


def test_decode_measurement_empty():
    measurement = {}

    payload = lora_custom_encoding.create_message("", measurement)

    assert len(payload) == 6 and payload == b"\xf4\x12\xfa\xc3\xb9\xc4"


def test_decode_vbatt():
    measurement = {"vbatt": {"value": 3675}}

    payload = lora_custom_encoding.create_message("", measurement)

    assert len(payload) == 10 and payload == b"\xf4\x12\xfa\xc3\xb9\xc4\x08\x10\x0e["


def test_device_id_override_is_used():
    payload = lora_custom_encoding.create_message("001122334455", {})

    assert payload == b"\x00\x11\x22\x33\x44\x55"


def test_uptime_is_4_bytes():
    measurement = {"uptime": {"value": 70000}}

    payload = lora_custom_encoding.create_message("", measurement)

    assert payload == b"\xf4\x12\xfa\xc3\xb9\xc4" + struct.pack(">BBI", 0x03, 0x10, 70000)


def test_signed_values_for_gps_and_formula():
    measurement = {
        "gps_lat": {"value": -12.34567},
        "gps_lon": {"value": -23.45678},
        "board_formula": {"value": -1.23456},
    }

    payload = lora_custom_encoding.create_message("", measurement)

    expected = b"\xf4\x12\xfa\xc3\xb9\xc4"
    expected += struct.pack(">BBi", 0x30, 0x10, -123456)
    expected += struct.pack(">BBi", 0xD1, 0x71, -1234567)
    expected += struct.pack(">BBi", 0xD2, 0x71, -2345678)

    assert payload == expected


def test_current_and_co2_scaling_matches_protocol():
    measurement = {
        "board_co2": {"value": 415},
        "board_current": {"value": 1.23},
    }

    payload = lora_custom_encoding.create_message("", measurement)

    expected = b"\xf4\x12\xfa\xc3\xb9\xc4"
    expected += struct.pack(">BBH", 0x13, 0x10, 415)
    expected += struct.pack(">BBH", 0x07, 0x10, 123)

    assert payload == expected


def test_pore_water_ec_uses_correct_type_and_no_divider():
    measurement = {"sdi12_0_pore_water_ec": {"value": 3210}}

    payload = lora_custom_encoding.create_message("", measurement)

    expected = b"\xf4\x12\xfa\xc3\xb9\xc4" + struct.pack(">BBH", 0x20, 0x50, 3210)

    assert payload == expected


def test_seq_and_diag_use_generic_4byte_format():
    measurement = {
        "board_seq": {"value": 12},
        "board_diag": {"value": 34},
    }

    payload = lora_custom_encoding.create_message("", measurement)

    expected = b"\xf4\x12\xfa\xc3\xb9\xc4"
    expected += struct.pack(">BBi", 0xE1, 0x10, 3400)
    expected += struct.pack(">BBi", 0xE0, 0x10, 1200)

    assert payload == expected


def test_adc_volt_float_is_encoded_without_failure():
    measurement = {"adc_adp1_volt": {"value": 1234.6}}

    payload = lora_custom_encoding.create_message("", measurement)

    expected = b"\xf4\x12\xfa\xc3\xb9\xc4" + struct.pack(">BBH", 0x16, 0x40, 1235)

    assert payload == expected


def test_wind_direction_float_is_encoded_as_degrees():
    measurement = {"meter_1_wind_direction": {"value": 273.4}}

    payload = lora_custom_encoding.create_message("", measurement)

    expected = b"\xf4\x12\xfa\xc3\xb9\xc4" + struct.pack(">BBH", 0x2D, 0x51, 2734)

    assert payload == expected


def test_4_20_alias_location_uses_current_channel_location():
    measurement = {"4_20_1_current": {"value": 4.2}}

    payload = lora_custom_encoding.create_message("", measurement)

    expected = b"\xf4\x12\xfa\xc3\xb9\xc4" + struct.pack(">BBH", 0x07, 0x61, 420)

    assert payload == expected


def test_pcnt_edge_count_uses_dedicated_type():
    measurement = {"pcnt_edge_count_1": {"value": 7}}

    payload = lora_custom_encoding.create_message("", measurement)

    expected = b"\xf4\x12\xfa\xc3\xb9\xc4" + struct.pack(">BBH", 0x40, 0x83, 7)

    assert payload == expected


def test_pcnt_period_s_maps_to_period_type():
    measurement = {"pcnt_period_s_1": {"value": 2.5}}

    payload = lora_custom_encoding.create_message("", measurement)

    expected = b"\xf4\x12\xfa\xc3\xb9\xc4" + struct.pack(">BBH", 0x2B, 0x83, 25)

    assert payload == expected


def test_adc_raw_maps_to_voltage_and_adp_location():
    measurement = {"adc_1_raw": {"value": 735.063}}

    payload = lora_custom_encoding.create_message("", measurement)

    expected = b"\xf4\x12\xfa\xc3\xb9\xc4" + struct.pack(">BBH", 0x16, 0x40, 735)

    assert payload == expected


def test_meter_count_vwc_is_encoded_as_count_type():
    measurement = {"meter_2_1_count_vwc": {"value": 1832.09}}

    payload = lora_custom_encoding.create_message("", measurement)

    expected = b"\xf4\x12\xfa\xc3\xb9\xc4" + struct.pack(">BBH", 0x29, 0x52, 18321)

    assert payload == expected


def test_modbus_uses_dedicated_location_and_float_type():
    measurement = {"modbus_1_1_uint16_f1_d0_msw1_le0": {"value": 2}}

    payload = lora_custom_encoding.create_message("", measurement)

    expected = b"\xf4\x12\xfa\xc3\xb9\xc4" + struct.pack(">BBf", 0x50, 0xB1, 2.0)

    assert payload == expected


def test_modbus_slave_id_is_masked_to_low_nibble():
    measurement = {"modbus_17_1_uint16_f1_d0_msw1_le0": {"value": 12.5}}

    payload = lora_custom_encoding.create_message("", measurement)

    expected = b"\xf4\x12\xfa\xc3\xb9\xc4" + struct.pack(">BBf", 0x50, 0xB1, 12.5)

    assert payload == expected


def test_audit_scenario_representative_numeric_measurements_are_encodable():
    # Representative numeric keys from scenario.py/scenario_utils.py,
    # scenario_digital_adc_utils.py, scenario_advind_utils.py,
    # scenario_enviro_utils.py/scenario_enviro_utils_custom_mpy.py,
    # scenario_pcnt_ulp.py, scenario_accel_utils.py and scenario_scale_utils.py.
    measurements = {
        "reset_cause": {"value": 1},
        "uptime": {"value": 123456},
        "vbatt": {"value": 3742},
        "board_temp": {"value": 24.25},
        "board_humidity": {"value": 55.20},
        "sht40_temp": {"value": 21.12},
        "sht40_humidity": {"value": 60.33},
        "scd30_co2": {"value": 415},
        "bme680_pressure": {"value": 1013},
        "bme680_gas": {"value": 1200},
        "adc_adp1_volt": {"value": 1244.4},
        "4-20_1_current": {"value": 4.35},
        "4_20_2_current": {"value": 19.85},
        "acclima_1_1_vwc": {"value": 31.12},
        "acclima_1_1_rel_perm": {"value": 12.34},
        "acclima_1_1_soil_ec": {"value": 2450},
        "acclima_1_1_pore_water_ec": {"value": 1530},
        "meter_1_solar": {"value": 612.2},
        "meter_1_precipitation": {"value": 3.4},
        "meter_1_wind_speed": {"value": 6.78},
        "meter_1_wind_direction": {"value": 273.4},
        "meter_1_air_temperature": {"value": 19.33},
        "meter_1_relative_humidity": {"value": 44.8},
        "meter_1_atmospheric_pressure": {"value": 101.3},
        "licor_1_1_et": {"value": 0.432},
        "licor_1_1_le": {"value": 52.6},
        "licor_1_1_h": {"value": 14.2},
        "licor_1_1_vpd": {"value": 11.7},
        "licor_1_1_pa": {"value": 1012.3},
        "licor_1_1_taf": {"value": 71.24},
        "licor_1_1_rh": {"value": 48.55},
        "licor_1_1_seq": {"value": 7},
        "licor_1_1_diag": {"value": 2},
        "implexx_1_1_sap_flow": {"value": 2.34},
        "implexx_1_1_hv_outer": {"value": 5.67},
        "implexx_1_1_hv_inner": {"value": 5.43},
        "implexx_1_1_log_rt_a_outer": {"value": -0.12345},
        "implexx_1_1_log_rt_a_inner": {"value": 0.23456},
        "pcnt_count_1": {"value": 14.2},
        "pcnt_period_s_1": {"value": 2.5},
        "pcnt_filtered_edges_1": {"value": 8},
        "pcnt_count_formula_1": {"value": 9.87654},
        "asm330_accX": {"value": 0.123},
        "asm330_accY": {"value": -0.456},
        "asm330_accZ": {"value": 1.234},
        "dev_is_operating": {"value": 1},
        "vibration_total": {"value": 0.987},
        "scale_weight": {"value": 512.34},
        "scale_temp": {"value": 28.25},
        "gps_lat": {"value": -12.34567},
        "gps_lon": {"value": 23.45678},
    }

    payload = lora_custom_encoding.create_message("", measurements)

    assert isinstance(payload, (bytes, bytearray))
    assert len(payload) > 6
    assert payload[:6] == b"\xf4\x12\xfa\xc3\xb9\xc4"


def test_audit_unknown_numeric_keys_fall_back_to_generic_without_failure():
    measurements = {
        "mystery_metric": {"value": 12.34},
        "another_metric_2": {"value": -4.56},
    }

    payload = lora_custom_encoding.create_message("", measurements)

    assert isinstance(payload, (bytes, bytearray))
    assert len(payload) > 6
    assert payload[:6] == b"\xf4\x12\xfa\xc3\xb9\xc4"
