import unittest
from unittest.mock import patch
from insighioNode.apps.demo_console.scenario_enviro_utils import parse_modbus_response


class TestParseModbusResponse(unittest.TestCase):
    def test_parse_modbus_response_uint16(self):
        response = [0x1234]
        result = parse_modbus_response(response, "uint16", 1, 0, True, False)
        self.assertEqual(result, 0x1234)

    def test_parse_modbus_response_int16(self):
        response = [0xFFFF]
        result = parse_modbus_response(response, "int16", 1, 0, True, False)
        self.assertEqual(result, -1)

    def test_parse_modbus_response_uint32(self):
        response = [0x1234, 0x5678]
        result = parse_modbus_response(response, "uint32", 1, 0, True, False)
        self.assertEqual(result, 0x12345678)

    def test_parse_modbus_response_int32(self):
        response = [0xFFFF, 0xFFFF]
        result = parse_modbus_response(response, "int32", 1, 0, True, False)
        self.assertEqual(result, -1)

    def test_parse_modbus_response_float(self):
        response = [0x3F80, 0x0000]  # 1.0 in IEEE 754
        result = parse_modbus_response(response, "float", 1, 0, True, False)
        self.assertAlmostEqual(result, 1.0, places=5)

    def test_parse_modbus_response_with_factor(self):
        response = [0x000A]
        result = parse_modbus_response(response, "uint16", 2, 0, True, False)
        self.assertEqual(result, 20)

    def test_parse_modbus_response_with_decimal_digits(self):
        response = [0x000A]
        result = parse_modbus_response(response, "uint16", 1, 2, True, False)
        self.assertEqual(result, 0.1)

    def test_parse_modbus_response_little_endian(self):
        response = [0x1234, 0x5678]
        result = parse_modbus_response(response, "uint32", 1, 0, True, True)
        self.assertEqual(result, 0x56781234)

    def test_parse_modbus_response_invalid_format(self):
        response = [0x1234]
        with self.assertLogs(level="ERROR") as log:
            result = parse_modbus_response(response, "invalid_format", 1, 0, True, False)
            self.assertIsNone(result)
            self.assertIn("Unsupported MODBUS format", log.output[0])

    def test_parse_modbus_response_msw_first_false(self):
        response = [0x1234, 0x5678]
        result = parse_modbus_response(response, "uint32", 1, 0, False, False)
        self.assertEqual(result, 0x56781234)


if __name__ == "__main__":
    unittest.main()
