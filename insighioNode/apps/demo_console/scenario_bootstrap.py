import logging
import utils
import device_info
from . import cfg


def execute(useExistingConfiguration=False):
    from . import wifi as network

    network.init(cfg)  # ?
    logging.debug("Network modules loaded")

    connection_results = network.connect(cfg)
    is_connected = "status" in connection_results

    _DEVICE_ID = device_info.get_device_id()[0]
    cfg.set("device_id", _DEVICE_ID)
    cfg.set("_SECRET_KEY", "000000000000000000000")

    headers = {"Authorization": cfg.get("_SECRET_KEY"), "accept": "application/json"}
    URL_base = "console.insigh.io"
    URL_PATH = "/things/bootstrap/{}".format(_DEVICE_ID)
    url = "{}://{}{}".format("http" if device_info.get_hw_module_verison() == "esp32wroom" else "https", URL_base, URL_PATH)

    try:
        from utils import httpclient

        client = httpclient.HttpClient(headers)
        response = client.get(url)
        if response and response.status_code == 200:
            try:
                resp = response.content.decode("utf-8")
                if resp.startswith('"') and resp.endswith('"'):
                    resp = resp[1:-1]
                logging.debug("new configuration: " + resp)
                import json

                obj = json.loads(resp)
                logging.debug("loaded object: {}".format(obj))
                iid = obj["mainflux_id"]
                ikey = obj["mainflux_key"]
                iData = (
                    obj["mainflux_channels"][0]["id"]
                    if obj["mainflux_channels"][0]["name"] == "data"
                    else obj["mainflux_channels"][1]["id"]
                )
                iControl = (
                    obj["mainflux_channels"][1]["id"]
                    if obj["mainflux_channels"][1]["name"] == "control"
                    else obj["mainflux_channels"][0]["id"]
                )

                keyValueDict = dict()
                if useExistingConfiguration:
                    # check if configuration needs change
                    try:
                        protocol_config = cfg.get_protocol_config()
                        if (
                            protocol_config.message_channel_id == iData
                            and protocol_config.control_channel_id == iControl
                            and protocol_config.thing_id == iid
                            and protocol_config.thing_token == ikey
                        ):
                            logging.info("Bootstrap: no change")
                            return False
                        logging.info("New device keys detected, about to apply configuration")
                        from www import stored_config_utils

                        keyValueDict = stored_config_utils.get_config_values(False, True)
                        logging.debug("loaded keys: {}".format(keyValueDict))
                    except Exception as e:
                        logging.exception(e, "error while processing bootstrap data")
                        return False
                else:
                    keyValueDict["selected-board"] = (
                        "old_esp_abb_panel" if device_info.get_hw_module_verison() == "esp32wroom" else "ins_esp_abb_panel"
                    )
                    keyValueDict["network"] = "wifi"
                    keyValueDict["wifi-ssid"] = list(frozenset([key for key in cfg.get("_CONF_NETS")]))[0]
                    keyValueDict["wifi-pass"] = cfg.get("_CONF_NETS")[keyValueDict["wifi-ssid"]]["pwd"]
                    keyValueDict["protocol"] = "mqtt"
                    keyValueDict["system-enable-ota"] = "True"

                keyValueDict["insighio-id"] = iid
                keyValueDict["insighio-key"] = ikey
                keyValueDict["insighio-channel"] = iData
                keyValueDict["insighio-control-channel"] = iControl

                from utils import configuration_handler

                if "content" in obj:
                    keyValueDictContent = configuration_handler.stringParamsToDict(obj["content"])
                    if keyValueDictContent is not None:
                        keyValueDict.update(keyValueDictContent)

                logging.info("about to apply: {}".format(keyValueDict))
                configuration_handler.notifyServerWithNewConfig()
                configuration_handler.apply_configuration(keyValueDict)

                logging.info("about to reboot to apply new config")
                from machine import reset

                reset()

                return resp
            except Exception as e:
                logging.exception(e, " error reading response")
    except Exception as e:
        logging.exception(e, "error trying to execute bootstrap HTTP GET")

    network.deinit()

    utils.deleteModule("utils.httpclient")

    logging.error("failed to execute bootstrap")
    return False
