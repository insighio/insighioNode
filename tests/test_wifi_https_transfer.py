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


class TestWifiHttpConsumers(unittest.TestCase):
    def setUp(self):
        self.module_patch = patch.dict(sys.modules, {})
        self.module_patch.start()
        self.addCleanup(self.module_patch.stop)

        httpclient = types.ModuleType("utils.httpclient")
        httpclient.HttpClient = Mock()
        utils = types.ModuleType("utils")
        utils.httpclient = httpclient
        utils.deleteModule = Mock()
        device_info = types.ModuleType("device_info")
        device_info.get_hw_module_verison = Mock(return_value="esp32s3")
        device_info.get_device_id = Mock(return_value=("device", None))
        sys.modules.update({"utils": utils, "utils.httpclient": httpclient, "device_info": device_info})
        self.httpclient = httpclient
        self.utils = utils

    def test_ota_fallback_closes_failed_https_response(self):
        from insighioNode.apps.demo_console import ota

        failed = Mock(status_code=503)
        succeeded = Mock(status_code=200)
        self.httpclient.HttpClient.return_value.get.side_effect = [failed, succeeded]
        with patch.object(ota.gc, "mem_free", return_value=1024, create=True):
            response = ota._http_get_with_fallback("https://console.insigh.io/path")

        self.assertIs(response, succeeded)
        failed.close.assert_called_once()
        self.assertEqual(
            [call.args[0] for call in self.httpclient.HttpClient.return_value.get.call_args_list],
            ["https://console.insigh.io/path", "http://console.insigh.io/path"],
        )
        response.close()

    def test_ota_delete_closes_response_and_unloads_client(self):
        from insighioNode.apps.demo_console import ota

        config = types.SimpleNamespace(thing_id="device", control_channel_id="control", thing_token="secret")
        response = Mock(status_code=200)
        self.httpclient.HttpClient.return_value.delete.return_value = response
        with patch.object(ota.cfg, "get_protocol_config", return_value=config):
            self.assertTrue(ota.delete_action(types.SimpleNamespace(modem_based=False), "action"))

        response.close.assert_called_once()
        self.utils.deleteModule.assert_called_once_with("utils.httpclient")

    def test_ota_control_get_closes_response_and_unloads_client(self):
        from insighioNode.apps.demo_console import ota

        response = Mock(status_code=200, content=b'"[]"')
        self.httpclient.HttpClient.return_value.get.return_value = response
        config = types.SimpleNamespace(thing_token="secret")
        with patch.object(ota.cfg, "get_protocol_config", return_value=config), patch.object(
            ota.gc, "mem_free", return_value=1024, create=True
        ):
            content = ota._fetch_control_content(
                types.SimpleNamespace(modem_based=False), "/mf-rproxy/device/pending-actions", "id=device", "tmpactions"
            )

        self.assertEqual(content, "[]")
        response.close.assert_called_once()
        self.utils.deleteModule.assert_called_once_with("utils.httpclient")

    def test_ota_download_handles_failed_fallback(self):
        from insighioNode.apps.demo_console import ota

        self.httpclient.HttpClient.return_value.get.side_effect = [OSError("TLS failed"), OSError("HTTP failed")]
        config = types.SimpleNamespace(server_ip="console.insigh.io", thing_id="device", thing_token="secret", control_channel_id="control")
        with patch.object(ota, "hasEnoughFreeSpace", return_value=True), patch.object(
            ota.device_info, "get_device_root_folder", return_value="/tmp/", create=True
        ), patch.object(ota.cfg, "get_protocol_config", return_value=config), patch.object(
            ota.gc, "mem_free", return_value=1024, create=True
        ), patch.object(
            ota.logging, "exception"
        ):
            self.assertIsNone(ota.downloadOTA(types.SimpleNamespace(modem_based=False), "file", ".bin", 12))

        self.assertEqual(self.httpclient.HttpClient.return_value.get.call_count, 2)
        self.utils.deleteModule.assert_called_once_with("utils.httpclient")

    def test_bootstrap_failed_response_closes_and_unloads_client(self):
        wifi = types.ModuleType("insighioNode.apps.demo_console.wifi")
        wifi.init = Mock()
        wifi.connect = Mock(return_value={"status": {"value": True}})
        wifi.deinit = Mock()
        sys.modules[wifi.__name__] = wifi
        from insighioNode.apps.demo_console import scenario_bootstrap

        response = Mock(status_code=401)
        self.httpclient.HttpClient.return_value.get.return_value = response
        with patch.object(scenario_bootstrap.cfg, "get", return_value="secret"), patch.object(scenario_bootstrap.cfg, "set"):
            self.assertFalse(scenario_bootstrap.execute())

        response.close.assert_called_once()
        self.utils.deleteModule.assert_called_once_with("utils.httpclient")
        wifi.deinit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
