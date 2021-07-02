import utime
from machine import Pin, UART
from modem_mc60 import ModemMC60

uart1 = UART(1)
uart1.init(115200, bits=8, parity=None, stop=1, tx=19, rx=18, timeout=500, timeout_char=1000)

modem = ModemMC60(uart1)
modem.init()

modem.print_status()

print("stating gps")
modem.set_gps_state(True)
print("is gps on: " + str(modem.is_gps_on()))
print("stating to search for gps signal")
modem.get_gps_position()

print("Waiting for registration...")
registration_status = modem.wait_for_registration()
print("Registration status: ", registration_status)

if registration_status:
    modem.connect()
    if modem.is_connected():
        # open sockets and send data
        pass
    modem.disconnect()
