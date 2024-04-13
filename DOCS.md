# Home Assistant Add-on: Comfort to MQTT

## Installation

The installation of this add-on is pretty straightforward and no different in comparison to other manually installed Home Assistant add-ons.

1. In Home Assistant, go to `Settings` -> `Add-ons` and click the `ADD-ON STORE` button.

2. Once in the ADD-ON STORE, click the three dots `...` in the top-right corner and select `Repositories`

3. Paste the ```https://github.com/djagerif/comfort2mqtt``` URL on the line provided and click `ADD`.

4. When the Add-on URL is successfully loaded you can click `Close`.

  After a few seconds you should now see the following Add-on. If not, navigate back to `Settings`, go to `Add-ons` -> `Add-on Store` once again.

  ![image](https://github.com/djagerif/comfort2mqtt/assets/5621764/fd7b947d-3787-4a13-a0f1-78e45e1ba9a0)

Even though this is a mostly Python implementation, it's currently only tested on an amd64 platform. It has been developed on 64-bit Alpine Linux, other platforms remain untested and it's not clear if it will work or not.

:information_source: **Please note:** This add-on requires configuration to connect with Home Assistant and Comfort II Ultra alarm system.


## Home Assistant Configuration

Manual Sensor creation is required in your `configuration.yaml` file before this Add-on can start. Sample object configurations are shown below.

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
Please take note of the `Study Light` example above. Comfort II Ultra supports both 8-bit and Signed 16-bit values but many integrations, like Clipsal C-BUS, uses 8-bit values and sets Counter values to EG. 0xFF(255) for 'On' and 0x00(0) for 'Off' state. If you have a Comfort II Ultra integration that is different to the example above then adjust your `On` integer value accordingly.


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
[mosquitto]: https://mosquitto.org/


## Add-on Configuration

**Note**: _Remember to restart the add-on when the configuration is changed._

### Option: `MQTT Broker Address` (Optional)

The `MQTT Broker Address` is the Hostname or IP address of the MQTT Broker used by both Home Assistant and the Comfort to MQTT Add-on. By default the hostname is `core-mosquitto` but can be changed if required.

### Option: `MQTT Broker Username`

The Username with Read/Write priveledges in MQTT that will be used for connection authentication. For more information on Users and Rights, please refer to the Home Assistant Mosquitto Add-on documentation or the Mosquitto [Homepage][mosquitto].

### Option: `MQTT Broker Password`

Password used for the above configured user for MQTT session establishment.

### Option: `MQTT Broker Port` (Optional)

The MQTT Broker listener port. This can be any configured port on your MQTT Broker. Please check your MQTT Broker Network configuration on what ports are configured. The default value is `1883`.

### Option: `MQTT Transport Protocol` (Optional)

The MQTT Transport Protocol between the Add-on and MQTT Broker can either be `TCP` or `WebSockets`. The default is `TCP`.

### Option: `MQTT Transport Encryption` (Optional) - Not currently used

The MQTT traffic can be encrypted with `TLS` or sent in clear-text. The Encryption option is currently not available. The default is `False`

### Option: `Comfort II Port` (Optional)

The Comfort II Ultra UCM/Eth03 TCP port used for connectivity. UCM/ETh03 can be changed so please check your Comfort II Ultra configuration and use the port that is configured for access. Note that only one client can connect to any given TCP port. The default is '1002'

### Option: `Comfort II IP address`

The Comfort II Ultra UCM/Eth03 IP address or Hostname used for connectivity.

### Option: `Comfort II User Login ID`

Cytech Comfort II User Login ID with the appropriate rights. Login ID has minimum 4 characters and 6 maximum. For full functionality you need at least Local Arm/Disarm and Remote Arm/Disarm capabilities on Comfort. See the Comfigurator [Programming Guide][progman],  `Security Settings` and `Sign-in Codes` sections for more information on user creation and rights.

[progman]: http://www.cytech.biz/download_files.php?item_id=1082

### Option: `Global Log Verbosity` (Optional)

This option controls the level of log output by the addon and can be changed to be more or less verbose, which might be useful when you are dealing with an unknown issue. Possible values are:

- `DEBUG`:   Shows detailed debug information.
- `ERROR`:   Runtime errors that do not require immediate action.
- `WARNING`: Exceptional occurrences that are not errors.
- `INFO`:    Normal (usually) interesting events.

Please note that each level automatically includes log messages from a more severe level, e.g. `DEBUG` also shows `INFO` messages. By default, the `log_level` is set to `INFO`, which is the recommended setting unless you are troubleshooting.

### Option: `Comfort II Zone Inputs` - Under Development

Set number of Input zones.

### Option: `Comfort II Zone Outputs` - Under Development

Set number of Output zones.

### Option: `Comfort II SCS/RIO Inputs` - Under Development

Set number of SCS/RIO Inputs.

### Option: `Comfort II SCS/RIO Outputs` - Under Development

Set number of SCS/RIO Outputs.

### Option: `Comfort II Responses` (Optional)

This sets the number of Responses that the Add-on subscribes to. Valid range values are from 0 - 1024. If you subscribe to the first 100 responses and trigger a response number EG. 200, then it will not be sent to Comfort for execution. Only subscribed responses are executed. The Default value is `0`.

### Option: `Set Comfort II Time and Date` (Optional)

Set the Comfort II Ultra Time and Date when the Add-on logs in and then 00:00 every day. The default value is `False`.


## Support

Got questions?

- The [Comfort Forums][comfortforums] for any questions or suggestions


## Authors & contributors

The original source for this project was done by [koocyrat][koochyrat]. This project is a modified, and slightly extended version, of the same source project.


## License (Summary)

```                    GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

                            Preamble

  The GNU General Public License is a free, copyleft license for
software and other kinds of works.

  The licenses for most software and other practical works are designed
to take away your freedom to share and change the works.  By contrast,
the GNU General Public License is intended to guarantee your freedom to
share and change all versions of a program--to make sure it remains free
software for all its users.  We, the Free Software Foundation, use the
GNU General Public License for most of our software; it applies also to
any other work released this way by its authors.  You can apply it to
your programs, too.<snip>```

More details can be obtained from [gnu.org][license].

[license]: https://www.gnu.org/licenses/gpl-3.0.en.html
[comfort2mqtt]: https://github.com/djagerif/comfort2mqtt
[koochyrat]: https://github.com/koochyrat/comfort2
[comfortforums]: http://https://comfortforums.com/
