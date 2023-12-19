# boot.py -- run on boot-up

# if on battery, enable this for early low voltage detection.
import gpio_handler
#
print("---Checking Voltage")
gpio_handler.check_minimum_voltage_threshold(3300)
print("---Voltage OK")
