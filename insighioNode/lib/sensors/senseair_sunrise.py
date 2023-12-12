import utime
import sensors
import ustruct
from machine import Pin, SoftI2C


# parameters
sunrise_addr_hex = "0x68"


def get_reading(sda_pin, scl_pin, enable_pin, ready_pin, vcc_pin=None):
    co2 = None
    temp = None

    sensors.set_sensor_power_on(vcc_pin)

    try:
        # init
        sunrise_addr = int(sunrise_addr_hex, 16)
        i2c = SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin), freq=40000)
        en_pin = Pin(enable_pin, Pin.OUT)
        nRDY_pin = Pin(ready_pin, Pin.IN, Pin.PULL_UP)

        # single-meas
        # Step 1: Drive en pin high
        en_pin.on()

        # Step 2: Wait for 35ms
        utime.sleep_ms(35)

        # Step 3: Start Meas Command & Sensor State Data
        i2c.writeto(sunrise_addr, b"", False)
        utime.sleep_ms(5)
        i2c.writeto(sunrise_addr, b"\x93\x01", True)

        # Step 4: Wait for falling edge on nRDY or for 2.4s
        max_delay_ms = 2400
        deadline = utime.ticks_add(utime.ticks_ms(), max_delay_ms)
        while nRDY_pin.value() and utime.ticks_diff(deadline, utime.ticks_ms()) > 0:
            pass
        print("nRDY falling edge detected after {} msec ".format(max_delay_ms - utime.ticks_diff(deadline, utime.ticks_ms())))
        utime.sleep_ms(2400)

        # Step 5: Read CO2 Value
        i2c.writeto(sunrise_addr, b"", False)
        utime.sleep_ms(5)
        i2c.writeto(sunrise_addr, b"\x06", True)
        read_bytes = i2c.readfrom(sunrise_addr, 2)
        co2 = ustruct.unpack(">h", read_bytes)[0]
        # print("Bytes read: {}, CO2 = {} ppm".format(read_bytes, co2))

        # Step 5b: read temp
        i2c.writeto(sunrise_addr, b"", False)
        utime.sleep_ms(5)
        i2c.writeto(sunrise_addr, b"\x08", True)
        read_bytes = i2c.readfrom(sunrise_addr, 2)
        temp = 0.01 * ustruct.unpack(">h", read_bytes)[0]
        # print("Bytes read: {}, Temp = {} deg".format(read_bytes, temp)

        en_pin.off()
    except Exception as e:
        pass

    sensors.set_sensor_power_off(vcc_pin)

    return (co2, temp)
