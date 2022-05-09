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

# for ESP32 devices
ROOT_PATH=""
# for Pycom devices
#ROOT_PATH="/flash"

ampy -p /dev/ttyUSB0 -b 115200 put apps $ROOT_PATH/apps
ampy -p /dev/ttyUSB0 -b 115200 put boot.py $ROOT_PATH/boot.py
ampy -p /dev/ttyUSB0 -b 115200 put lib $ROOT_PATH/lib
ampy -p /dev/ttyUSB0 -b 115200 put main.py $ROOT_PATH/main.py
ampy -p /dev/ttyUSB0 -b 115200 put web_server.py $ROOT_PATH/web_server.py
ampy -p /dev/ttyUSB0 -b 115200 put www $ROOT_PATH/www
```

## Configure

The configuration of the device operation, security keys, network connection etc. can be done through the implemented [Web UI configuration wizard](https://docs.insigh.io/gettingstarted/configuration/).

After following the [Getting Started](https://docs.insigh.io/gettingstarted/) steps, the device will be ready to measure and upload!

# Future Work

* Security enhancements (TLS)
* < Name your desired feature! >

# Issues

In case of bug reports or feature requests feel free to open an [issue](https://github.com/insighio/insighioNode/issues).
