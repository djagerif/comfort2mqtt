# Home Assistant Add-on: Comfort to MQTT
Cytech Comfort to MQTT bridge for Home Assistant.

![Supports aarch64 Architecture][aarch64-shield] ![Supports amd64 Architecture][amd64-shield] ![Supports armhf Architecture][armhf-shield] ![Supports armv7 Architecture][armv7-shield] ![Supports i386 Architecture][i386-shield]

[mosquitto]: https://mosquitto.org
[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg
<script type="text/javascript" src="https://cdnjs.buymeacoffee.com/1.0.0/button.prod.min.js" data-name="bmc-button" data-slug="IngoDeJager" data-color="#FFDD00" data-emoji="☕"  data-font="Cookie" data-text="Buy me a coffee" data-outline-color="#000000" data-font-color="#000000" data-coffee-color="#ffffff" ></script>

For more information about Cytech Comfort systems, please see the [Cytech Technology Pte Ltd.][cytech] website.

If you find this AddOn useful, consider buying me a <a href="https://www.buymeacoffee.com/IngoDeJager" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>.

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

⚠️ This Add-on was specifically developed for the Comfort II ULTRA Alarm System with File System type `34`. As tested firmware is `7.201` on model CM9000-ULT.

Copyright 2024 Ingo de Jager. Licensed under Apache-2.0. For more details see the `LICENCE` file.
