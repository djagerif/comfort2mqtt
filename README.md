# Home Assistant Add-on: Comfort to MQTT
Cytech Comfort II Ultra Alarm System to MQTT bridge for Home Assistant.

![Supports aarch64 Architecture][aarch64-shield] ![Supports amd64 Architecture][amd64-shield] ![Supports armhf Architecture][armhf-shield] ![Supports armv7 Architecture][armv7-shield] ![Supports i386 Architecture][i386-shield]

[mosquitto]: https://mosquitto.org
[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg

For more information about Cytech Comfort II Ultra alarm systems, please see the [Cytech Technologies Pte Ltd.][cytech] website.

[koochyrat]: https://github.com/koochyrat/comfort2
[cytech]: http://www.cytech.biz/index.html

## About
This Addon is used to bridge an IP connected Cytech Comfort II Ultra Alarm system to MQTT for use in Home Assistant.

⚠️ This software is neither certified nor endorsed by Cytech Technology Pte Ltd.

This is a customised version of the original comfort2mqtt project by `koochyrat`. More information about the original source project is available [here][koochyrat].

This implementation does not do auto configuration. Objects need to be manually configured in Home Assistant.

The following objects are currently supported:

* Zone Inputs [1-128]
* Zone Outputs [1-128]
* Counters [0-254]
* Flags [1-254]
* Sensors [0-31]
* RIO Outputs [129-248]
* RIO Inputs [129-248]
* Timer Reports [1-64]
* Responses [1-1024]

<p align="center">
    <img src="[http://material-bread.org/logo-shadow.svg](https://github.com/djagerif/comfort2mqtt/assets/5621764/64abe350-6b37-4b79-8fea-12fa5e89353a)" alt="Comfort II Ultra Keypad">
</p>

⚠️ This Add-on was specifically developed for the Comfort II Ultra range of Alarm Systems with File System type `34`. Firmware as tested, is `7.201`.
Copyright 2024 Ingo de Jager. Licensed under the GNU LGPL3+. For more details see `COPYING` and `COPYING.LESSER`.
