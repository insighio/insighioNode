import dht
import sensors
from machine import Pin
import logging


def get_reading(data_pin, dht_model, vcc_pin=None):
    """Returns temperature & humidity reading, for given VCC and DATA pins"""
    temp = None
    hum = None

    try:
        sensors.set_sensor_power_on(vcc_pin)

        # measurement
        th = None
        if dht_model == "DHT11":
            th = dht.DHT11(Pin(data_pin))
        elif dht_model == "DHT22":
            th = dht.DHT22(Pin(data_pin))

        if th:
            th.measure()
            temp = th.temperature()
            hum = th.humidity()

        sensors.set_sensor_power_off(vcc_pin)
    except Exception as e:
        logging.exception(e, "error reading DHT sensor")

    return (temp, hum)
