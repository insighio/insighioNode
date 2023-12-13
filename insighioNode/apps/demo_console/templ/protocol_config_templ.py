"""Transport-related configuration options """
protocol = "<protocol>"

protocol_config_instance = None


def get_protocol_config():
    global protocol_config_instance
    if protocol_config_instance is not None:
        return protocol_config_instance

    if protocol == "coap":
        from protocols import coap_client
        from protocols import coap_config

        protocol_config = coap_config.CoAPConfig()
        protocol_config.server_port = 5683
        protocol_config.use_custom_socket = _IP_VERSION == "IPV6"
    elif protocol == "mqtt":
        from protocols import mqtt_client
        from protocols import mqtt_config

        protocol_config = mqtt_config.MQTTConfig()
        protocol_config.server_port = 1884  # only for mqtt
        protocol_config.use_custom_socket = False
    else:
        print("Not supported transport protocol. Choose between CoAP and MQTT")
        return None

    if _IP_VERSION == "IPV6":
        protocol_config.server_ip = "2001:41d0:701:1100:0:0:0:2060"
    else:
        protocol_config.server_ip = "console.insigh.io"

    """ console.insigh.io security keys """
    protocol_config.message_channel_id = "<insighio-channel>"
    protocol_config.control_channel_id = "<insighio-control-channel>"
    protocol_config.thing_id = "<insighio-id>"
    protocol_config.thing_token = "<insighio-key>"
    protocol_config_instance = protocol_config
    return protocol_config
