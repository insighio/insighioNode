import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


def make_transport():
    httpclient = types.ModuleType("utils.httpclient")
    httpclient.HttpClient = Mock()
    utils = types.ModuleType("utils")
    utils.httpclient = httpclient
    wifi = types.ModuleType("networking.wifi")
    wifi.is_connected = Mock(return_value=True)
    networking = types.ModuleType("networking")
    networking.wifi = wifi
    sys.modules["utils"] = utils
    sys.modules["utils.httpclient"] = httpclient
    sys.modules["networking"] = networking
    sys.modules["networking.wifi"] = wifi

    from insighioNode.apps.demo_console.transfer_protocol import TransferProtocolHTTPS

    protocol_config = types.SimpleNamespace(
        keepalive=None,
        server_ip="console.insigh.io",
        message_channel_id="data",
        control_channel_id="control",
        thing_id="device",
        thing_token="secret",
    )
    cfg = Mock()
    cfg.get_protocol_config.return_value = protocol_config
    cfg.get.side_effect = lambda key: {"device_id": "device", "protocol": "mqtt"}[key]
    client = TransferProtocolHTTPS(cfg)
    return client, httpclient.HttpClient, wifi


class TestWifiHttpsTransfer(unittest.TestCase):
    def setUp(self):
        self.module_patch = patch.dict(sys.modules, {})
        self.module_patch.start()
        self.addCleanup(self.module_patch.stop)

    def test_posts_measurements_and_control(self):
        client, http_client, wifi = make_transport()
        response = Mock(status_code=201)
        http_client.return_value.post.return_value = response

        self.assertTrue(client.connect())
        self.assertTrue(client.send_packet('[{"n":"temp","v":1}]'))
        self.assertTrue(client.send_control_packet('[{"n":"e","v":9}]', "/configResponse"))

        headers = {"Authorization": "secret", "Content-Type": "application/json"}
        self.assertEqual([call.args for call in http_client.call_args_list], [(headers,), (headers,)])
        self.assertEqual(
            http_client.return_value.post.call_args_list[0].args,
            ("https://console.insigh.io/http/channels/data/messages/device",),
        )
        self.assertEqual(http_client.return_value.post.call_args_list[0].kwargs, {"data": b'[{"n":"temp","v":1}]'})
        self.assertEqual(
            http_client.return_value.post.call_args_list[1].args,
            ("https://console.insigh.io/http/channels/control/messages/device/configResponse",),
        )
        self.assertEqual(response.close.call_count, 2)
        wifi.is_connected.assert_called()

    def test_failed_response_and_disconnected_link(self):
        client, http_client, wifi = make_transport()
        response = Mock(status_code=401)
        http_client.return_value.post.return_value = response

        self.assertTrue(client.connect())
        self.assertFalse(client.send_packet("[]"))
        response.close.assert_called_once()

        wifi.is_connected.return_value = False
        self.assertFalse(client.send_packet("[]"))
        self.assertEqual(http_client.return_value.post.call_count, 1)

        client.disconnect()
        self.assertFalse(client.connected)

    def test_http_client_writes_authenticated_json(self):
        socket = Mock()
        socket.readline.side_effect = [b"HTTP/1.0 201 Created\r\n", b"\r\n"]
        usocket = types.ModuleType("usocket")
        usocket.SOCK_STREAM = 1
        usocket.getaddrinfo = Mock(return_value=[(1, 1, 1, None, ("console.insigh.io", 443))])
        usocket.socket = Mock(return_value=socket)
        ussl = types.ModuleType("ussl")
        ussl.wrap_socket = Mock(return_value=socket)
        device_info = types.ModuleType("device_info")
        device_info.wdt_reset = Mock()
        sys.modules.update({"usocket": usocket, "ussl": ussl, "device_info": device_info})

        filename = pathlib.Path(__file__).resolve().parents[1] / "insighioNode/lib/utils/httpclient.py"
        spec = importlib.util.spec_from_file_location("wifi_httpclient_test", filename)
        module = importlib.util.module_from_spec(spec)
        with patch("builtins.const", lambda value: value, create=True):
            spec.loader.exec_module(module)

        response = module.HttpClient({"Authorization": "secret", "Content-Type": "application/json"}).post(
            "https://console.insigh.io/http/channels/data/messages/device", data=b"[]"
        )
        self.assertEqual(response.status_code, 201)
        payload = socket.write.call_args.args[0]
        self.assertIn(b"Authorization: secret\r\n", payload)
        self.assertIn(b"Content-Type: application/json\r\n", payload)
        self.assertIn(b"Content-Length: 2\r\n", payload)
        self.assertTrue(payload.endswith(b"[]"))
        response.close()
        socket.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
