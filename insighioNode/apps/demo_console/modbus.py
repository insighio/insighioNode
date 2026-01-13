import logging
import uasyncio

from . import cfg

modbus_instance = None

_IS_ASYNCIO = False

lock = None
if _IS_ASYNCIO:
    lock = uasyncio.Lock()
else:
    import _thread

    lock = _thread.allocate_lock()


def init_instance(rtu_pins, baudrate=9600, data_bits=8, parity=None, stop_bits=1):
    global modbus_instance
    uart_id = 1

    from external.umodbus.serial import Serial as ModbusRTUMaster

    logging.debug("rtu_pins type: {}, rtu_pins: {}".format(type(rtu_pins), rtu_pins))
    logging.debug("baudrate type: {}, baudrate: {}".format(type(baudrate), baudrate))
    logging.debug("data_bits type: {}, data_bits: {}".format(type(data_bits), data_bits))
    logging.debug("uart_id type: {}, uart_id: {}".format(type(uart_id), uart_id))
    logging.debug("parity type: {}, parity: {}".format(type(parity), parity))
    logging.debug("stop_bits type: {}, stop_bits: {}".format(type(stop_bits), stop_bits))

    try:
        modbus_instance = ModbusRTUMaster(
            pins=rtu_pins,  # given as tuple (TX, RX)
            baudrate=baudrate,  # optional, default 9600
            data_bits=data_bits,  # optional, default 8
            stop_bits=stop_bits,  # optional, default 1
            parity=parity,  # optional, default None
            ctrl_pin=2,  # optional, control DE/RE
            uart_id=uart_id,  # optional, default 1, see port specific documentation
        )
    except Exception as e:
        logging.exception(e, "unable to initalize modbus communication")
    return modbus_instance


# def get_instance():
#     global modbus_instance
#     if modbus_instance is not None:
#         return modbus_instance
#     # _UC_IO_RCV_OUT = 9
#     # _UC_IO_DRV_IN = 7
#     _UC_IO_RCV_OUT = 17  # 41
#     _UC_IO_DRV_IN = 1  # 17
#     uart_id = 2
#     baudrate = 9600 #if cfg.get("_WEATHER_STATION_IS_FULL_FEATURE") == False else 4800
#
#     from external.umodbus.serial import Serial as ModbusRTUMaster
#
#     rtu_pins = (_UC_IO_DRV_IN, _UC_IO_RCV_OUT)  # (TX, RX)
#
#     logging.debug("rtu_pins: {}".format(rtu_pins))
#
#     try:
#         modbus_instance = ModbusRTUMaster(
#             pins=rtu_pins,  # given as tuple (TX, RX)
#             baudrate=baudrate,  # optional, default 9600
#             data_bits=8,  # optional, default 8
#             stop_bits=1,  # optional, default 1
#             parity=None,  # optional, default None
#             ctrl_pin=2,  # optional, control DE/RE
#             uart_id=uart_id,  # optional, default 1, see port specific documentation
#         )
#     except Exception as e:
#         logging.exception(e, "unable to initalize modbus communication")
#     return modbus_instance


def send_modbus_write(op_code, slave_addr, starting_addr, value, is_signed=False):
    global modbus_instance
    global lock
    if modbus_instance is None:
        logging.error("modbus instance is not yet initialized")
        return None

    with lock:
        try:
            if op_code == 5:
                modbus_instance.write_single_coil(slave_addr, starting_addr, value)
                return True
            elif op_code == 6:
                modbus_instance.write_single_register(slave_addr, starting_addr, value, is_signed)
                return True
            elif op_code == 15:
                values = value.split(",")
                ints = []
                for v in values:
                    ints.append(int(v, 16))
                modbus_instance.write_multiple_coils(slave_addr, starting_addr, ints)
                return True
            elif op_code == 16:
                values = value.split(",")
                ints = []
                for v in values:
                    ints.append(int(v, 16))
                modbus_instance.write_multiple_registers(slave_addr, starting_addr, ints, is_signed)
                return True
            else:
                return False

            logging.debug("register_value: {}".format(register_value))

        except Exception as e:
            logging.exception(
                e,
                "failed writing| op_code: {}, slave_addr: {}, measurement_reg_addr: {}, value: {}, is_signed: {}".format(
                    op_code, slave_addr, starting_addr, value, is_signed
                ),
            )
        return False


def send_modbus_read(op_code, slave_addr, starting_addr, quantity, is_signed=False):
    global modbus_instance
    global lock
    if modbus_instance is None:
        logging.error("modbus instance is not yet initialized")
        return None

    with lock:
        register_value = None

        try:
            if op_code == 1:
                register_value = modbus_instance.read_coils(slave_addr, starting_addr, quantity)
            elif op_code == 2:
                register_value = modbus_instance.read_discrete_inputs(slave_addr, starting_addr, quantity)
            elif op_code == 3:
                register_value = modbus_instance.read_holding_registers(slave_addr, starting_addr, quantity, is_signed)
            elif op_code == 4:
                register_value = modbus_instance.read_input_registers(slave_addr, starting_addr, quantity, is_signed)
            else:
                register_value = None

            # if quantity == 1 and register_value:
            #     register_value = register_value[0]

            logging.debug("register_value: {}".format(register_value))

        except Exception as e:
            logging.exception(
                e,
                "failed reading| op_code: {}, slave_addr: {}, measurement_reg_addr: {}, register_qty: {}, is_signed: {}".format(
                    op_code, slave_addr, starting_addr, quantity, is_signed
                ),
            )
        return register_value
