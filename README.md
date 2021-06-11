# insighioNode

The core libraries, utilities and application scenario for [insigh.io nodes](https://insigh.io/iot-nodes/) to operate with [insigh.io console](https://console.insigh.io)

The project is based on MicroPython and tested on Pycom and ESP32 devices.

# API reference

A complete description of all the supported APIs along with tutorials can be found in [insigh.io docs](https://docs.insigh.io).

# How to use

First thing first, clone repository and get all required submodules:

    ```bash
    git clone https://github.com/insighio/insighioNode

    cd insighioNode
    git submodule update --init --recursive
    ```

## Code upload via [Pymakr](https://pycom.io/products/supported-networks/pymakr/)

1. Install Pymakr addon for VSCode or Atom
1. Open project folder `insighioNode/insighioNode`
1. Upload the code

## Code upload via [ampy](https://github.com/scientifichackers/ampy)

[ampy](https://github.com/scientifichackers/ampy) is a command line tool to operate on micropython devices. To upload the code follow the commands:

```bash
cd insighioNode/insighioNode
# for Pycom devices
sudo  ampy -p /dev/ttyUSB0 -b 115200 put . /flash

# for ESP32 devices
sudo  ampy -p /dev/ttyUSB0 -b 115200 put . /
```
