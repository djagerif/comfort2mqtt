# Home Assistant Add-on: Comfort to MQTT

[Comfort to MQTT][comfort2mqtt] is a MQTT bridge between an IP network connected Comfort II Ultra Alarm Panel from Cytech and Home Assistant MQTT Broker EG. Mosquito. It provides the ability to configure various sensors in Home Assistant to monitor most of the objects available in the Comfort II Ultra alarm system. If you are using a different MQTT broker then update the configuration accordingly.

This is a customised version of the original comfort2mqtt project by [koochyrat].

[koochyrat]: https://github.com/koochyrat/comfort2

This implementation does not do auto configuration of objects in Home Asistant. Objects need to be manually configured in Home Assistant configuration.yaml. Samples of sensor configurations are shown below.

## Installation

The installation of this add-on is pretty straightforward and not different in comparison to other manually installed Home Assistant add-ons.

1. In Home Assistant, go to `Settings` -> `Add-ons` and click the `ADD-ON STORE` button.

2. Once in the ADD-ON STORE page click the three dots `...` in the top-right corner and select `Repositories`

3. Add the `https://github.com/djagerif/comfort2mqtt` URL and click `ADD`.

4. When the Add-on URL is loaded you can click `Close`.

  After a few seconds you should now see the following Add-on. If not then navigate back to `Settings` and go `Add-ons` -> `Add-on Store`.

  ![image](https://github.com/djagerif/comfort2mqtt/assets/5621764/fd7b947d-3787-4a13-a0f1-78e45e1ba9a0)


:information_source: Please note, the add-on requires configuration to connect with Home Assistant and the Comfort II Ultra alarm system.


## About this project

This is a customised version of the original comfort2mqtt project by [koochyrat]

[koochyrat]: https://github.com/koochyrat/comfort2

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

Manual Sensor creation is required in your configuration.yaml file. Samples are shown below.

```
mqtt: 
  alarm_control_panel:
    - name: Comfort Alarm
      unique_id: "comfort2_alarm"
      state_topic: "comfort2/alarm"
      command_topic: "comfort2/alarm/set"
      availability_topic: "comfort2/alarm/online"
      payload_available: "1"
      payload_not_available: "0"
      code: "1234"  # Code can be different from Comfort's. This code is for the Add-on while the Comfort code is to login to Comfort itself.
                    # Note: If the Comfort User Code does not allow Disarm then the Add-on will not be able to Disarm.
      
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
Please take note of the 'Study Light' example above. Comfort supports both 8-bit and Signed 16-bit values but many integrations, like Clipsal C-BUS, uses 8-bit values and sets Counter values to EG. 0xFF(255) for 'On' and 0x00(0) for 'Off' state. If you have a Comfort integration that is different to the example above then adjust your `On` integer value accordingly.

Even though this is a mostly Python implementation, it's currently only tested on an amd64 platform. It has been developed on 64-bit Alpine Linux, other platforms remain untested and it's not clear if it will work or not.

## Hardware interface support

The following Cytech Universal Communications Modules (UCM) Ethernet modules are supported:

* [UCM/Eth01] - Obsolete/Untested

* [UCM/Eth02] - Obsolete/Untested

* [UCM/Wifi01] - Not Recommended (WiFi)

* [UCM/Eth03] - Recommended (LAN)

  This software _requires_ a fully functional UCM/Ethernet or UCM/Wifi configuration. The UCM/Wifi is not recommended due to possible connectivity issues that could arise from switching between different AP's and other possible sources of RF noise. For best performance it is recommended to use the UCM/Eth03 which uses a physical LAN connection. Use a good quality CAT5e or better cable between the UCM/Eth03 and your network device.

  You must also have a reachable IP address on your network from Home Assistant to the Comfort II ethernet module (UCM). The default port is TCP/1002 which is Port #2 of a UCMEth03. If you have a segmented network with Firewalls then please ensure the required ports are open for communications.
  
  :information_source: **Note:** The UCM/WiFi uses port TCP/3000 as the default port. Any port may be used as long as there are no overlaps with existing services on the network.


[ha-auto]: https://www.home-assistant.io/docs/mqtt/discovery/
[ha-mqtt]: https://www.home-assistant.io/integrations/light.mqtt/#json-schema
[clipsal-docs]: https://updates.clipsal.com/ClipsalSoftwareDownload/DL/downloads/OpenCBus/OpenCBusProtocolDownloads.html
[libcbm-src]: https://sourceforge.net/projects/cbusmodule/files/source/
[py2]: https://www.python.org/doc/sunset-python-2/


## Add-on Configuration

**Note**: _Remember to restart the add-on when the configuration is changed._

### Option: `log_level`

The `log_level` option controls the level of log output by the addon and can
be changed to be more or less verbose, which might be useful when you are
dealing with an unknown issue. Possible values are:

- `trace`: Show every detail, like all called internal functions.
- `debug`: Shows detailed debug information.
- `info`: Normal (usually) interesting events.
- `warning`: Exceptional occurrences that are not errors.
- `error`: Runtime errors that do not require immediate action.
- `fatal`: Something went terribly wrong. Add-on becomes unusable.

Please note that each level automatically includes log messages from a
more severe level, e.g., `debug` also shows `info` messages. By default,
the `log_level` is set to `info`, which is the recommended setting unless
you are troubleshooting.

These log level also affects the log levels of the AppDaemon.

### Option: `system_packages`

Allows you to specify additional [Alpine packages][alpine-packages] to be
installed to your AppDaemon setup (e.g., `g++`. `make`, `ffmpeg`).

**Note**: _Adding many packages will result in a longer start-up time
for the add-on._

### Option: `python_packages`

Allows you to specify additional [Python packages][python-packages] to be
installed to your AppDaemon setup (e.g., `PyMySQL`. `Requests`, `Pillow`).

**Note**: _Adding many packages will result in a longer start-up time
for the add-on._

#### Option: `init_commands`

Customize your environment even more with the `init_commands` option.
Add one or more shell commands to the list, and they will be executed every
single time this add-on starts.

## AppDaemon and HADashboard configuration

This add-on does not configure the AppDaemon or HADashboard for you.
It does, however, create some sample files to get you started on the first run.

The configuration of the AppDaemon can be found in the add-on configuration
folder of this add-on.

For more information about configuring AppDaemon, please refer to the
extensive documentation they offer:

<http://appdaemon.readthedocs.io/en/latest/>

## Home Assistant access tokens and ha_url settings

By default, this add-on ships without a `token` and without the `ha_url`
in the `appdaemon.yaml` config file. **This is not an error!**

The add-on takes care of these settings for you and you do not need to provide
or set these in the AppDaemon configuration.

This automatic handling of the URL and token conflicts with the AppDaemon
official documentation. The official documentation will state `ha_url` and
`token` options are required. For the add-on, these aren't needed.

However, you are free to set them if you want to override, however, in
general usage, that should not be needed and is not recommended for this add-on.

## Changelog & Releases

This repository keeps a change log using [GitHub's releases][releases]
functionality.

Releases are based on [Semantic Versioning][semver], and use the format
of `MAJOR.MINOR.PATCH`. In a nutshell, the version will be incremented
based on the following:

- `MAJOR`: Incompatible or major changes.
- `MINOR`: Backwards-compatible new features and enhancements.
- `PATCH`: Backwards-compatible bugfixes and package updates.

## Support

Got questions?

You have several options to get them answered:

- The [Home Assistant Community Add-ons Discord chat server][discord] for add-on
  support and feature requests.
- The [Home Assistant Discord chat server][discord-ha] for general Home
  Assistant discussions and questions.
- The Home Assistant [Community Forum][forum].
- Join the [Reddit subreddit][reddit] in [/r/homeassistant][reddit]

You could also [open an issue here][issue] GitHub.

## Authors & contributors

The original setup of this repository is by [Franck Nijhof][frenck].

For a full list of all authors and contributors,
check [the contributor's page][contributors].

## License

MIT License

Copyright (c) 2021 - 2024 Franck Nijhof

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

[addon-badge]: https://my.home-assistant.io/badges/supervisor_addon.svg
[addon]: https://my.home-assistant.io/redirect/supervisor_addon/?addon=comfort2mqtt&repository_url=https%3A%2F%2Fgithub.com%2Fdjagerif%2Fcomfort2mqtt
[alpine-packages]: https://pkgs.alpinelinux.org/packages
[appdaemon]: https://appdaemon.readthedocs.io
[comfort2mqtt]: https://github.com/djagerif/comfort2mqtt
[contributors]: https://github.com/hassio-addons/addon-appdaemon/graphs/contributors
[discord-ha]: https://discord.gg/c5DvZ4e
[discord]: https://discord.me/hassioaddons
[forum]: https://community.home-assistant.io/t/home-assistant-community-add-on-appdaemon-4/163259?u=frenck
[frenck]: https://github.com/frenck
[issue]: https://github.com/hassio-addons/addon-appdaemon/issues
[python-packages]: https://pypi.org/
[reddit]: https://reddit.com/r/homeassistant
[releases]: https://github.com/hassio-addons/addon-appdaemon/releases
[semver]: http://semver.org/spec/v2.0.0.htm
