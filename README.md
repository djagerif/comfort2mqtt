# Comfort to MQTT

![Supports aarch64 Architecture][aarch64-shield] ![Supports amd64 Architecture][amd64-shield] ![Supports armhf Architecture][armhf-shield] ![Supports armv7 Architecture][armv7-shield] ![Supports i386 Architecture][i386-shield]

For more information on MQTT and Mosquitto, please see [mosquitto]

[mosquitto]: https://mosquitto.org
[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg

[![Documentation Status](https://readthedocs.org/projects/cbus/badge/?version=latest)][rtd] - Still to do !!

This Addon is used to bridge an IP connected Cytech Comfort II Ultra Alarm system to MQTT for use with Home Assistant.

Copyright 2024 Ingo de Jager. Licensed under the GNU LGPL3+. For more
details see `COPYING` and `COPYING.LESSER`.

> **Note:** This software is neither certified nor endorsed by Cytech
> Technology Pte Ltd.

More information about the original source project is available [here][koochyrat], and in the `docs` directory of the source
repository.

## About this project

This is a customised version of the original comfort2mqtt project by [koochyrat]

[koochyrat]: https://github.com/koochyrat/comfort2

This implementation does not do auto discovery. Objects need to be manually configured
in Home Assistant.

The following objects are currently supported:

* Zone Inputs [1-128]
* Zone Outputs [1-128]
* Counters [0-254]
* Flags [1-254]
* Sensors [0-31]
* RIO Outputs [129-248]
* RIO Inputs [129-248]
* Timer Reports [1-64]

Manual Sensor creation is required in your configuration.yaml file. Samples are shown below.

```
mqtt: 
  sensor:
    - name: Alarm Mode
      unique_id: 'comfort2_alarm_mode'
      availability_topic: "comfort2/alarm/online"
      state_topic: "comfort2/alarm"
      payload_available: "1"
      payload_not_available: "0"

  binary_sensor: 
    - name: Study PIR 
      unique_id: 'comfort2_input35' 
      state_topic: "comfort2/input35" 
      availability_topic: "comfort2/alarm/online" 
      payload_on: "1" 
      payload_off: "0" 
      payload_available: "1" 
      payload_not_available: "0" 
      device_class: motion

  switch:
    - name: Study Light
      unique_id: 'comfort2_counter201'
      state_topic: "comfort2/counter201"
      command_topic: "comfort2/counter201/set"
      availability_topic: "comfort2/alarm/online"
      payload_on: "255"
      payload_off: "0"
      payload_available: "1"
      payload_not_available: "0"
```
Please take note of the 'Study Light' example above. Comfort supports 16-bit values but 
many integrations set counter values to 0xFF(255) as an 'On' state.

Even though this is a Python implementation, it's currently only tested on
an amd64 platform. It has been developed on Linux on `amd64`, other platforms
remain untested and it's not clear if it will work.

## Hardware interface support

This should work with the following Cytech Ethernet modules (UCM):

* [UCM/Eth01] - Obsolete

* [UCM/Eth02] - Obsolete

* [UCM/Wifi01] - Not Recommended (WiFi)

* [UCM/Eth03] - Recommended (LAN)

  This software _requires_ a fully functional UCM/Ethernet or UCM/Wifi configuration.
  The UCM/Wifi is not recommended due to possible connectivity issues that could arise from 
  switching between AP's and other possible sources of noise. It is recommended to use the 
  UCM/Eth03 with LAN cable implementation.

  You must have a reachable IP address on your network from Home Assistant to Comfort II
  UCM/Eth03. The default port is TCP/1002 which is Port #2 of an existing UCM/Eth03. 
  Other UCM's may require a different port number.

[rtd]: https://cbus.readthedocs.io/en/latest/
[coveralls]: https://coveralls.io/github/micolous/cbus
[travis]: https://travis-ci.org/micolous/cbus
[5500PC]: https://www.clipsal.com/Trade/Products/ProductDetail?catno=5500PC
[5500PCU]: https://www.clipsal.com/Trade/Products/ProductDetail?catno=5500PCU
[5500CN]: https://updates.clipsal.com/ClipsalOnline/Files/Brochures/W0000348.pdf
[5500CN2]: https://www.clipsal.com/Trade/Products/ProductDetail?catno=5500CN2
[ha-auto]: https://www.home-assistant.io/docs/mqtt/discovery/
[ha-mqtt]: https://www.home-assistant.io/integrations/light.mqtt/#json-schema
[clipsal-docs]: https://updates.clipsal.com/ClipsalSoftwareDownload/DL/downloads/OpenCBus/OpenCBusProtocolDownloads.html
[libcbm-src]: https://sourceforge.net/projects/cbusmodule/files/source/
[py2]: https://www.python.org/doc/sunset-python-2/
