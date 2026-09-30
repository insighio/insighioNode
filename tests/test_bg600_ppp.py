import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


class FakeUART:
    def __init__(self):
        self.writes = []

    def write(self, data):
        self.writes.append(data)


class FakeBaseModem:
    def __init__(self, *args):
        self.uart = FakeUART()
        self.ppp = None
        self.connected = False
        self.apn = "test.apn"
        self.commands = []
        self.dial_result = False

    def connect(self, timeoutms=30000):
        if isinstance(self.dial_result, Exception):
            raise self.dial_result
        return self.dial_result

    def reset_uart(self):
        self.uart = FakeUART()

    def send_at_cmd(self, command, *args):
        self.commands.append(command)
        return True, ["+CGACT: 1,1"]


def load_bg600():
    base = types.ModuleType("networking.modem.modem_base")
    base.Modem = FakeBaseModem
    modem = types.ModuleType("networking.modem")
    modem.modem_base = base
    gps = types.ModuleType("external.micropyGPS.micropyGPS")
    gps.MicropyGPS = object
    device_info = types.ModuleType("device_info")
    device_info.wdt_reset = lambda: None
    device_info.get_device_id = lambda: ("test",)
    utime = types.ModuleType("utime")
    utime.sleep_ms = lambda milliseconds: None
    utime.ticks_ms = lambda: 0
    utime.ticks_diff = lambda first, second: first - second
    utime.ticks_add = lambda first, second: first + second
    modules = {
        "networking": types.ModuleType("networking"),
        "networking.modem": modem,
        "networking.modem.modem_base": base,
        "external": types.ModuleType("external"),
        "external.micropyGPS": types.ModuleType("external.micropyGPS"),
        "external.micropyGPS.micropyGPS": gps,
        "device_info": device_info,
        "utime": utime,
        "ure": types.ModuleType("ure"),
    }
    path = Path(__file__).parents[1] / "insighioNode/lib/networking/modem/modem_bg600.py"
    with patch.dict(sys.modules, modules):
        spec = importlib.util.spec_from_file_location("networking.modem.modem_bg600", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module.ModemBG600


class TestBG600PPP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.modem_type = load_bg600()

    def setUp(self):
        self.modem = self.modem_type(None, None, None, None)

    def test_default_uses_at(self):
        self.assertTrue(self.modem.connect())
        self.assertFalse(self.modem.data_over_ppp)
        self.assertIn("AT+QIACT=1", self.modem.commands)

    def test_ppp_success_uses_socket_session(self):
        self.modem.use_ppp = True
        self.modem.dial_result = True
        self.assertTrue(self.modem.connect())
        self.assertTrue(self.modem.data_over_ppp)
        self.assertEqual(self.modem.commands, [])

    def test_failed_ppp_restores_at(self):
        self.modem.use_ppp = True
        uart = self.modem.uart
        self.assertTrue(self.modem.connect())
        self.assertEqual(uart.writes, ["+++"])
        self.assertFalse(self.modem.data_over_ppp)
        self.assertIn("AT+QIACT=1", self.modem.commands)

    def test_ppp_setup_exception_restores_at(self):
        self.modem.use_ppp = True
        self.modem.dial_result = RuntimeError("PPP unavailable")
        uart = self.modem.uart
        with patch.object(self.modem_type.connect.__globals__["logging"], "exception"):
            self.assertTrue(self.modem.connect())
        self.assertEqual(uart.writes, ["+++"])
        self.assertFalse(self.modem.data_over_ppp)

    def test_ppp_teardown_restores_at_before_modem_shutdown(self):
        class FakePPP:
            def __init__(self):
                self.active_state = True

            def active(self, state):
                self.active_state = state

        self.modem.ppp = FakePPP()
        self.modem.connected = True
        uart = self.modem.uart
        self.modem.disconnect()
        self.assertFalse(self.modem.connected)
        self.assertIsNone(self.modem.ppp)
        self.assertEqual(uart.writes, ["+++"])
        self.assertIn("AT+QIDEACT=1", self.modem.commands)


if __name__ == "__main__":
    unittest.main()
