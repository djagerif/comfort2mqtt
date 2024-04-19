# Home Assistant Add-on: Comfort to MQTT

## Installation

The installation of this add-on is pretty straightforward and no different in comparison to other manually installed Home Assistant add-ons.

1. In Home Assistant, go to `Settings` -> `Add-ons` and click the `ADD-ON STORE` button.

2. Once in the ADD-ON STORE, click the three dots `...` in the top-right corner and select `Repositories`

3. Paste the ```https://github.com/djagerif/comfort2mqtt``` URL on the line provided and click `ADD`.

4. When the Add-on URL is successfully loaded you can click `Close`.

  After a few seconds you should now see the following Add-on. If not, navigate back to `Settings`, go to `Add-ons` -> `Add-on Store` once again.

![image](https://github.com/djagerif/comfort2mqtt/assets/5621764/181c6e31-8210-4fb1-9e30-f69a3a416e20)


Even though this is a mostly Python implementation, it's currently only tested on an amd64 platform. It has been developed on 64-bit Alpine Linux, other platforms remain untested and it's not clear if it will work or not.

**Please note:** This add-on requires configuration to connect with Home Assistant and Comfort II Ultra alarm system.


## Home Assistant Configuration

Manual Sensor creation is required in your `configuration.yaml` file before this Add-on can start. 

It must be noted that Comfort requires the `#` key during arming to acknowledge and bypass any open zones. Because the `Home Assistant Alarm Control Panel` does not have a`#` key, the `CUSTOM BYPASS` key is utilised for that purpose and send the appropriate `#` keycode (KD1A) to Comfort.

Sample object configurations are shown below.

```
mqtt: 
  alarm_control_panel:
    - name: Comfort Alarm
      unique_id: "comfort2_alarm_a46ee0"        # E.G. Use last six digits of UCM/Eth03 MAC address to make it unique
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

    - name: Alarm Message
      unique_id: 'comfort2_alarm_message'
      state_topic: "comfort2/alarm/message"
      availability_topic: "comfort2/alarm/online"
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

  light:
    - name: Kitchen Light (Dimmable)
      unique_id: 'comfort2_counter117'
      state_topic: "comfort2/counter117/state"
      command_topic: "comfort2/counter117/set"
      availability_topic: "comfort2/alarm/online"
      payload_on: 1
      payload_off: 0
      payload_available: 1
      payload_not_available: 0
      brightness_scale: 255
      brightness_state_topic: "comfort2/counter117"
      brightness_command_topic: "comfort2/counter117/set"
      optimistic: false
      on_command_type: "brightness"

    - name: Study Light (Non Dimmable On|Off)
      unique_id: 'comfort2_counter201'
      state_topic: "comfort2/counter201"
      command_topic: "comfort2/counter201/set"
      availability_topic: "comfort2/alarm/online"
      payload_on: 255
      payload_off: 0
      payload_available: 1
      payload_not_available: 0
      optimistic: false
      on_command_type: "first"
```
Comfort II Ultra supports both Unsigned 8-bit and Signed 16-bit values. However, many integrations like Clipsal C-BUS uses Unsigned 8-bit values and sets Counter values to send 0xFF(255) for the 'On' and 0x00(0) for the 'Off' state. If you have a Comfort II Ultra integration that is different to the example above then adjust your `payload_on` and `payload_off` integer values accordingly.

The `Kitchen Light` is an example of a Dimmable light and the `Study Light` is a Non-Dimmable light both mapped to their respective Comfort Counters. You could also map your Non-Dimmable Lights to Comfort Flags instead which would operate in the same manner as Counters except the `payload_on`value will be `1` rather than `255`.

Because `Counters` can be used for many things other than Lights, the `Kitchen Light` in the example follows the [Brightness Without On Commands][ha-mqtt] chapter in the Home Assistant MQTT Light documentation, with a few additions.


## Hardware and Interface support

This Add-on was specifically developed for the Comfort II Ultra range of Alarm Systems with File System type `34`. Comfort II Ultra firmware as tested is `7.201`. If any other Comfort system, model or firmware other than `7.201`, is used then results may be unexpected.

The following Cytech Universal Communications Modules (UCM) Ethernet modules are supported:

* [UCM/Eth01] - Obsolete/Untested

* [UCM/Eth02] - Obsolete/Untested

* [UCM/Wifi01] - Not Recommended (WiFi) - Firmware 7.176

* [UCM/Eth03] - Recommended (LAN) - Firmware 7.176

This software _requires_ a fully functional UCM/Ethernet or UCM/Wifi configuration with inactivity timeouts set to default values of 2 minutes. The UCM/Wifi is not recommended due to possible connectivity issues that could arise from switching between different AP's or other possible sources of RF noise. For best performance it is recommended to use the UCM/Eth03 which uses a physical LAN connection. Use a good quality CAT5e or better cable between the UCM/Eth03 and your network device.

If your network is segmented using a firewall, or any other device, you must ensure all applicable ports are allowed between Home Assistant and the Comfort II Ethernet Module (UCM). The default port for the UCM/Eth03 is TCP/1002 which is Port #2 of a UCMEth03.
  
**Note:** The UCM/WiFi uses port TCP/3000 as the default port. Any port may be used as long as there are no overlaps with existing services on the network.

[ha-auto]: https://www.home-assistant.io/docs/mqtt/discovery/
[ha-mqtt]: https://www.home-assistant.io/integrations/light.mqtt/#brightness-without-on-commands
[mosquitto]: https://mosquitto.org/


## Add-on Configuration


### Option: `MQTT Broker Address` (Optional)

The `MQTT Broker Address` is the Hostname, or IP address, of the MQTT Broker used by both Home Assistant and the Comfort to MQTT Add-on. By default the hostname is `core-mosquitto`. If another MQTT Broker is used then this needs to reflect the IP address or Hostname of that instance.

### Option: `MQTT Broker Username`

The Username with Read/Write priveledges in MQTT that will be used for connection authentication. For more information on Users and Rights, please refer to the Home Assistant Mosquitto Add-on documentation or the Mosquitto [Homepage][mosquitto].

### Option: `MQTT Broker Password`

Password used for the MQTT Broker Username. Used for authenticated MQTT session establishment.

### Option: `MQTT Broker Port` (Optional)

The MQTT Broker exposed listener port. This can be any configured port on your MQTT Broker. Please check your MQTT Broker Network configuration on what exposed ports are configured. The default value is `1883`. Take note that Mosquitto Broker port configurations are Docker `exposed` ports. These ports will not reflect in any Mosquitto Broker logs as it uses e.g. 1883 internally for TCP and 1884 for WebSockets.

### Option: `MQTT Transport Protocol` (Optional)

The MQTT Transport Protocol between the Add-on and MQTT Broker can either be `TCP` or `WebSockets`. The default is `TCP`.

### Option: `Comfort II Ultra Port` (Optional)

The Comfort II Ultra UCM/Eth03 TCP port used for connectivity. UCM/ETh03 can be changed so please check your Comfort II Ultra configuration and use the port that is configured for access. Note that only one client can connect to any given TCP port. The default is '1002'

### Option: `Comfort II Ultra IP address`

The Comfort II Ultra UCM/Eth03 IP address or Hostname used for connectivity.

### Option: `Comfort II Ultra User Login ID`

Cytech Comfort II User Login ID with the appropriate rights. Login ID has minimum 4 characters and 6 maximum. For full functionality you need at least Local Arm/Disarm and Remote Arm/Disarm capabilities on Comfort. See the [Comfigurator Programming Guide][progman], `Security Settings` and `Sign-in Codes` sections for more information on user creation and rights.

[progman]: http://www.cytech.biz/download_files.php?item_id=1082

### Option: `Global Log Verbosity` (Optional)

This option controls the level of log output by the addon and can be changed to be more or less verbose, which might be useful when you are dealing with an unknown issue. Possible values are:

- `DEBUG`:   Shows detailed debug information.
- `ERROR`:   Runtime errors that do not require immediate action.
- `WARNING`: Exceptional occurrences that are not errors.
- `INFO`:    Normal, usually, interesting events (`DEFAULT`).

Please note that each level automatically includes log messages from a more severe level, e.g. `DEBUG` also shows `INFO` messages. By default, the `log_level` is set to `INFO`, which is the recommended setting unless you are troubleshooting.

### Option: `Comfort II Ultra Zone Inputs` - Under Development

Set number of Input zones.

### Option: `Comfort II Ultra Zone Outputs` - Under Development

Set number of Output zones.

### Option: `Comfort II Ultra SCS/RIO Inputs` - Under Development

Set number of SCS/RIO Inputs.

### Option: `Comfort II Ultra SCS/RIO Outputs` - Under Development

Set number of SCS/RIO Outputs.

### Option: `Comfort II Ultra Responses` (Optional)

This sets the number of Responses that the Add-on subscribes to. Valid range values are from 0 - 1024. If you subscribe to the first 100 responses and trigger a response number EG. 200, then it will not be sent to Comfort for execution. Only subscribed responses are executed. The Default value is `0`.

### Option: `Set Comfort II Ultra Time and Date` (Optional)

Set Comfort II Ultra Time and Date when the Add-on logs in and automatically every day at midnight. The default value is `False`.


## Custom Zone Name File

a CSV file can be uploaded to the `addon_config` directory with the format as shown below. The first column is the `Zone Number` and the second column the `Zone Name`.

Upload a file called `zones.csv` to the `addon_config` directory and the Zone Names from the file will be used to enrich the logging information. The `zones.csv` file allows for up to 128 zones.

To upload a file to the `addon_config` directory you could use something like [Samba share][samba] Add-on or similar allowing filesystem access to seleced directories on Home Assistant.

[samba]:https://github.com/home-assistant/addons/tree/master/samba

```
1,FrontDoor
2,GarageDoor
3,GaragePIR
4,UtilityDoor
5,Long Description for Kitchen Door
6,Zone6
7,Zone7
8,Zone8
9,Zone9
10,Zone10
11,Zone11
.
.
.
127,Zone127
128,Zone128
```

Zone Name lengths are permitted up to 30 characters but restricted to the following characters `[a-zA-Z0-9 _-]`. Names can be enclosed in quotes but is optional. Zone numbers must be numerical and are limited from 1 to 128.

If you upload a file with incorrect `Zone Name` or `Number` information the file will be disregarded and an error message logged in the addon log file. If you upload a valid `zones.csv` file, but have not specified all the zones, only the zones with valid data will be used and the zones without will display the below message in the log file. As an example, on receipt of an `ER08` `Zone Open` message while arming or a Bypass Message when force-armed with an open zone.

2024-04-16 22:41:13 WARNING  Zone 8 Not Ready (**N/A**)


## Support

Got questions?

- The [Comfort Forums][comfortforums] for any questions or suggestions


## Authors & contributors

The original source for this project was done by [koocyrat][koochyrat]. This project is a modified, and slightly extended version, of the same source project.


## License (Summary)

```
                     GNU GENERAL PUBLIC LICENSE
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
your programs, too. <snip>
```

More details can be obtained from [gnu.org][license].

[license]: https://www.gnu.org/licenses/gpl-3.0.en.html
[comfort2mqtt]: https://github.com/djagerif/comfort2mqtt
[koochyrat]: https://github.com/koochyrat/comfort2
[comfortforums]: https://comfortforums.com/
