def device_info_get_device_id():
    return ("f412fac3b9c4", b"\xf4\x12\xfa\xc3\xb9\xc4")


import sys
import binascii

module = type(sys)("device_info")
module.get_device_id = device_info_get_device_id
sys.modules["device_info"] = module

sys.modules["ubinascii"] = binascii

# import sys
# module = type(sys)("my_module_name")
# module.submodule = type(sys)("my_submodule_name")
# module.submodule.something = sommething
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
