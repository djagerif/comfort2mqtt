# Home Assistant Add-on: Comfort to MQTT
Cytech Comfort to MQTT bridge for Home Assistant.

![Supports aarch64 Architecture][aarch64-shield] ![Supports amd64 Architecture][amd64-shield] ![Supports armhf Architecture][armhf-shield] ![Supports armv7 Architecture][armv7-shield] ![Supports i386 Architecture][i386-shield]

[mosquitto]: https://mosquitto.org
[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg

For more information about Cytech Comfort systems, please see the [Cytech Technology Pte Ltd.][cytech] website.

If you find this Add-on useful.  

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/ingodejager)

[koochyrat]: https://github.com/koochyrat/comfort2
[cytech]: http://www.cytech.biz/index.html

## About
This Addon is used to bridge an IP connected Cytech Comfort II ULTRA Alarm system to MQTT for use in Home Assistant. Other Comfort systems are partially supported but has not been tested.

⚠️ This software is neither certified nor endorsed by Cytech Technology Pte Ltd.

This is a customised version of the original comfort2mqtt project by `koochyrat`. More information about the original source project is available [here][koochyrat].

This implementation does minimal MQTT auto-discovery. Some `System` entities are created but all other objects need to be manually configured in Home Assistant as required.

The following objects are supported:

* Zone Inputs [1-96]
* Zone Outputs [1-96]
* Counters [0-254]
* Flags [1-254]
* Sensors [0-31]
* RIO Inputs [129-248]
* RIO Outputs [129-248]
* Responses [1-1024]

<div style="text-align:center"> <img src="https://github.com/djagerif/comfort2mqtt/assets/5621764/64abe350-6b37-4b79-8fea-12fa5e89353a" alt="Comfort II ULTRA Keypad"/> </div>

⚠️ This Add-on was specifically developed for Home Assistant OS and Comfort II ULTRA Alarm System with File System type `34`. As tested firmware is `7.201` on model CM9000-ULT. Home Assistant Container and Core have not been tested and is not supported at present.

Copyright 2026 Ingo de Jager. Licensed under Apache-2.0. For more details see the `LICENCE` file.
