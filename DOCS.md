# Home Assistant Add-on: Comfort to MQTT

## Installation

The installation of this add-on is pretty straightforward and no different in comparison to other manually installed Home Assistant add-ons.

1. In Home Assistant, go to `Settings` -> `Add-ons` and click the `ADD-ON STORE` button.

2. Once in the ADD-ON STORE, click the three dots `...` in the top-right corner and select `Repositories`

3. Paste the ```https://github.com/djagerif/comfort2mqtt``` URL on the line provided and click `ADD`.

4. When the Add-on URL is successfully loaded you can click `Close`.

  After a few seconds you should now see the following Add-on. If not, navigate back to `Settings`, go to `Add-ons` -> `Add-on Store` once again.

![image](https://github.com/djagerif/comfort2mqtt/assets/5621764/181c6e31-8210-4fb1-9e30-f69a3a416e20)


Even though this is a mostly Python implementation, it's currently only tested on an amd64 platform. It has been developed on 64-bit Alpine Linux with other platforms remaining untested and it's unclear if it will work or not.

⚠️ This Add-on requires initial configuration to connect with Home Assistant and your Comfort systems.


## MQTT

The following MQTT topics are published:
```
comfort2mqtt/alarm - current MQTT alarm state (disarmed, pending, armed_home, armed_away, armed_night, arm_vacation, triggered)
comfort2mqtt/alarm/online - '1' for online, '0' for offline
comfort2mqtt/alarm/message - Informational messages, e.g. the zone that triggered an alarm
comfort2mqtt/alarm/timer - countdown entry/exit timer in seconds when arming to away mode or entering. updates every second.
comfort2mqtt/alarm/status - Status of the alarm (Idle, Trouble, Alert, Alarm)
comfort2mqtt/alarm/bypass - List of Bypassed zones. EG. 1,3,5,7,9. '0' indicates no bypassed zones.
comfort2mqtt/alarm/LWT - Online or Offline text status
comfort2mqtt/alarm/refresh - Trigger a refresh of all objects. Used when a refresh of all object states are required.
comfort2mqtt/alarm/connected - Status of LAN Connection to Comfort. '1' when connected and logged in.
comfort2mqtt/alarm/doorbell - '0' for off/answered or '1' for on
comfort2mqtt/alarm/mode - Integer values for current Alarm Mode. 0 - 4 (Off, Away, Night, Day, Vacation), See Comfort M? or MD documentation.
 comfort2mqtt/alarm/battery_status - ARM based systems support battery and dv 12v output sensors.

comfort2mqtt/input<1 to 96> (Zone Input) have the following JSON attributes EG.
{
  "Time": "2024-06-12T15:12:42",
  "Name": "GarageDoor",
  "ZoneWord": "Garage Door",
  "State": 0,
  "Bypass": 0
}

comfort2mqtt/input<129 to 248> (SCS/RIO Input) have the following JSON attributes EG.
{
  "Time": "2024-06-12T15:12:44",
  "Name": "ScsRioResp129",
  "ZoneWord": null,
  "State": 0,
  "Bypass": null
}

comfort2mqtt/output<1 to 96> (Zone Output) have the following JSON attributes EG.
{
  "Time": "2024-06-12T15:12:44",
  "Name": "Output01",
  "State": 0
}

comfort2mqtt/output<129 to 248> (SCS/RIO Output) have the following JSON attributes EG.
{
  "Time": "2024-06-12T15:12:45",
  "Name": "ScsRioOutput129",
  "State": 0
}

comfort2mqtt/flag<1 to 254> have the following JSON attributes EG.
{
  "Time": "2024-06-12T15:12:46",
  "Name": "Flag01",
  "State": 0
}

comfort2mqtt/sensor<0 to 31> have the following JSON attributes EG.
{
  "Time": "2024-06-12T17:16:54",
  "Name": "Sensor01",
  "Value": 0
}

comfort2mqtt/counter<0 to 254> have the following JSON attributes EG.
{
  "Time": "2024-06-12T15:12:49",
  "Name": "Counter000",
  "Value": 0,
  "State": 0
}
*Note:  'State' 1 for On, 0 for Off. State is set to 1 when Value is non-zero. Used for lighting 
        as this indicates On|Off status while Value could indicate brightness

```

The following MQTT topics are subscribed.

```
comfort2mqtt/alarm/set - sent from Home Assistant, DISARM, ARM_HOME, ARM_NIGHT, ARM_VACATION, ARM_AWAY or REM_ARM_AWAY.
                         ARM_CUSTOM_BYPASS is a special case and is used to send the # key instead.
comfort2mqtt/alarm/refresh - sent from Home Assistant, <Key> triggers a complete object refresh
comfort2mqtt/alarm/battery_update - sent from Home Assistant, <id> triggers a battery update query 'D?id01 and D?id02
                                    id's 0,1,33-37 are supported for Main and Slaves when ARM CPU is detected. 0 for bulk if supported.

comfort2mqtt/input<1 to 96>/set - 1 for open/active, 0 for closed/inactive. Settable if zone is a Virtual input
comfort2mqtt/input<129 to 248>/set

comfort2mqtt/output<1 to 96>/set - 0=off, 1=on, 2=change state , 3 = Pulse Output for 1 second, 4 - Flash Output at 1 sec On/Off rate
comfort2mqtt/output<129 to 248>/set

comfort2mqtt/response<1 to 1024>/set - value is ignored. Comfort response is activated as programmed in Comfigurator

comfort2mqtt/flag<1 to 254>/set - 1 for on, 0 for off

comfort2mqtt/counter<0 to 254>/set - 16-bit value

comfort2mqtt/sensor<0 to 31>/set - 16-bit value
```


## Home Assistant Configuration

Manual Sensor creation is required in your `configuration.yaml` file before this Add-on can start. 

![information](https://github.com/djagerif/comfort2mqtt/assets/5621764/2d0daafc-8499-4fc8-b93a-29505891087b) It must be noted that Comfort requires the `#` key during arming to acknowledge and bypass any open zones. Because the `Home Assistant Alarm Control Panel` does not have a native `#` key, the `CUSTOM BYPASS` key is utilised for that purpose and send the appropriate `#` keycode (`KD1A`) to Comfort.

Sample object configurations are shown below.

```
mqtt: 
  alarm_control_panel:
    - name: Comfort Alarm
      unique_id: "comfort2_alarm_a46ee0"
      object_id: "comfort2_alarm_a46ee0"        # E.G. Use last six digits of UCM/Eth03 MAC address to make it unique
      code_arm_required: false
      qos: 2
      supported_features:
        - arm_home
        - arm_away
        - arm_night
        # - arm_vacation
        - arm_custom_bypass
      state_topic: "comfort2mqtt/alarm"
      command_topic: "comfort2mqtt/alarm/set"
      availability_topic: "comfort2mqtt/alarm/online"
      payload_available: 1
      payload_not_available: 0
      code: "1234"  # Code can be different from Comfort's. This code is for the Add-on while the Comfort code is to login to Comfort itself.
                    # Note: If the Comfort User Code does not allow Disarm then the Add-on will not be able to Disarm.
                    # Secrets can be used EG. "code: !secret comfort_pin
      
  sensor:
    - name: Alarm Mode
      unique_id: "comfort2_alarm_mode"
      object_id: "comfort2_alarm_mode"
      availability_topic: "comfort2mqtt/alarm/online"
      state_topic: "comfort2mqtt/alarm"
      payload_available: "1"
      payload_not_available: "0"

    - name: Alarm Message
      unique_id: "comfort2_alarm_message"
      object_id: "comfort2_alarm_message"
      state_topic: "comfort2mqtt/alarm/message"
      availability_topic: "comfort2mqtt/alarm/online"
      payload_available: "1"
      payload_not_available: "0"

    - name: Main Bedroom Temperature
      unique_id: "comfort2_counter244"
      object_id: "comfort2_counter244"
      state_topic: "comfort2mqtt/counter244"
      availability_topic: "comfort2mqtt/alarm/online"
      value_template: "{{ value_json.Value }}"
      json_attributes_template: "{{ value_json | tojson }}"
      json_attributes_topic: "comfort2mqtt/counter244"
      device_class: temperature
      state_class: measurement
      unit_of_measurement: °C
      payload_available: "1"
      payload_not_available: "0"

  binary_sensor: 
    - name: Study PIR
      unique_id: "comfort2_input35"
      object_id: "comfort2_input35"
      state_topic: "comfort2mqtt/input35"
      availability_topic: "comfort2mqtt/alarm/online"
      value_template: '{{ value_json.State }}'
      json_attributes_topic: "comfort2mqtt/input35"
      json_attributes_template: '{{ value_json | tojson }}'
      payload_on: "1"
      payload_off: "0"
      payload_available: "1"
      payload_not_available: "0"
      device_class: motion

  light:
    - name: Kitchen Light
      unique_id: "comfort2_counter117"
      object_id: "comfort2_counter117"
      state_topic: "comfort2mqtt/counter117"
      state_value_template: '{{ value_json.State }}'
      command_topic: "comfort2mqtt/counter117/set"
      availability_topic: "comfort2mqtt/alarm/online"
      json_attributes_topic: "comfort2mqtt/counter117"
      json_attributes_template: '{{ value_json | tojson }}'
      payload_on: "1"
      payload_off: "0"
      payload_available: "1"
      payload_not_available: "0"
      brightness_scale: "255"
      brightness_value_template: '{{ value_json.Value }}'
      brightness_state_topic: "comfort2mqtt/counter117"
      brightness_command_topic: "comfort2mqtt/counter117/set"
      optimistic: false
      on_command_type: "brightness"

    - name: Study Light
      unique_id: "comfort2_counter201"
      object_id: "comfort2_counter201"
      state_topic: "comfort2mqtt/counter201"
      state_value_template: '{{ value_json.Value }}'
      command_topic: "comfort2mqtt/counter201/set"
      availability_topic: "comfort2mqtt/alarm/online"
      json_attributes_topic: "comfort2mqtt/counter201"
      json_attributes_template: '{{ value_json | tojson }}'
      payload_on: 255
      payload_off: 0
      payload_available: 1
      payload_not_available: 0
      optimistic: false
      on_command_type: "first"
```
![information](https://github.com/djagerif/comfort2mqtt/assets/5621764/2d0daafc-8499-4fc8-b93a-29505891087b) To Enable or Disable the various modes displayed on the Alarm Control Panel you need to edit the UI element and select the desired mode to be visible.

![image](https://github.com/user-attachments/assets/86418ce8-6042-480c-a5fd-1b888758ae0f)

Comfort II ULTRA supports both Unsigned 8-bit and Signed 16-bit values. However, many integrations like Clipsal C-BUS, by Schneider Electric, uses Unsigned 8-bit values and sets Counter values of 0xFF(255) for 'On' and 0x00(0) for 'Off' states and any other value in between when required for example dimming. If you have a Comfort II ULTRA integration that is different to the example mentioned then you need to adjust your `payload_on` and `payload_off` integer values accordingly.

The `Kitchen Light` is an example of a Dimmable light and the `Study Light` is a Non-Dimmable light, both mapped to their respective Comfort Counters. You could also map your Non-Dimmable Lights to Comfort Flags which should operate in a similar manner as Counters except the `payload_on`value will be `1` rather than `255`. With the Light examples above you can also add the `Brightness` secondary info to the Dimmer light icon and it will display as per below.

![image](https://github.com/djagerif/comfort2mqtt/assets/5621764/1d16931d-1cfd-4f55-83c0-16be5a90e777)

Because `Counters` can be used for other uses other than Lights, the `Kitchen Light` in the example follows the [Brightness Without On Commands][ha-mqtt] chapter in the Home Assistant MQTT Light documentation, with a few small tweaks.

### Auto-Discovered Objects

When the Add-on is fully configured and running, there will be two new MQTT Devices with several System Entities auto-discovered as per below. The values for these entities are retrieved from both the Comfort system as well as the alarm configuration `CCLX` file. If the `CCLX` file is not present then no object enrichment will be done and default names will be used for entities, especially ZoneWord strings and Object Descriptions as per the `CCLX` file.

![image](https://github.com/user-attachments/assets/faeaa08b-c8f6-43db-a946-46ee9762b35b)


## Home Assistant - Custom Card `#` (Optional)

The native `Alarm Control Panel` card does not include a `#` key for confirmation, you need to create a separate custom button card that can simulate the `#` key. One option is to install the Custom Button Card and then call 'arm_bypass' which is configured to send a `#` key code instead of arming into `Custom bypass` mode. The other option is to design your own card that incorporates this key. Below is the easiest option to follow.

1. Download the `Custom Button Card` from https://github.com/custom-cards/button-card and install it according to whichever method you prefer. Refer to the repository documentation for installation and configuration instructions for either manual or HACS installation.

2. Once installed, edit your dashboard and create new button using your newly installed custom button card. Below is a sample of the configuration that is required to make this button send a `#` key code to Comfort. Change the entity name to the one in your system.

```
type: custom:button-card
name: 'Comfort # Key'
icon: mdi:pound
color: rgb(28, 128, 199)
size: 10%
tap_action:
  action: call-service
  service: alarm_control_panel.alarm_arm_custom_bypass
  data:
    entity_id: alarm_control_panel.comfort_alarm
```

![information](https://github.com/djagerif/comfort2mqtt/assets/5621764/2d0daafc-8499-4fc8-b93a-29505891087b) The `Comfort to MQTT` Add-on changes the behaviour of the `Custom bypass` arm function and uses it to send the `#` key code instead. Please unselect the `Custom bypass` option when creating the `Alarm Control Panel` card.


## Home Assistant - Alarm State Colours (Optional)

The native `Alarm Control Panel` uses Grey, Orange and Green for Disarmed, Arming/Pending and Armed, Red is used for Triggered. These colours do not correlate with the Comfort II ULTRA Alarm states. To change the colours to use Green, Orange and Red, you have to add a separate `Theme` to your `Alarm Control Panel` card.

1. Create a file called `themes.yaml`, it can actually be named anything.yaml, it doesn't matter. Copy this file into your Home Assistant `/config/themes` directory. If the directory doesn't exist then create the directory.

2. Make sure your `configuration.yaml` file contains an include statement for this file or directory. If you have a directory inclusion then this file will be included automatically. Here is an example of a directory inclusion.

```
frontend:
  themes: !include_dir_merge_named themes
```

3. The contents of the themes.yaml file should look like the below. This is just a sample and might contain more than what is required, it is borrowed, with thanks, from the HA community around the topic of custom colours.

```
alarm:
  # Main colors
  state-alarm_control_panel-armed_home-color: "#F44336" # Red
  state-alarm_control_panel-armed_away-color: "#F44336" # Red
  state-alarm_control_panel-arming-color: "#FF9800" # Orange
  state-alarm_control_panel-disarmed-color: "#4CAF50" # Green
  state-alarm_control_panel-pending-color: "#FF9800" # Orange
  state-alarm_control_panel-triggered-color: "#F44336" # Red
  state-alert-color: "#F44336" # Red
  # Main colors
  primary-color: "#5294E2" # Header
  accent-color: "#E45E65" # Accent color
  dark-primary-color: "var(--accent-color)" # Hyperlinks
  light-primary-color: "var(--accent-color)" # Horizontal line in about
  #
  # Text colors
  primary-text-color: "#FFFFFF" # Primary text colour, here is referencing dark-primary-color
  text-primary-color: "var(--primary-text-color)" # Primary text colour
  secondary-text-color: "#5294E2" # For secondary titles
  ```

3. Lastly, edit your `Alarm Control Panel` card and assign the new `alarm` theme to it. This will change the Alarm State colours to reflect what Comfort uses.


## Home Assistant - 'Refresh' Automation (Optional)

When Home Assistant Restarts (Not Reload), it only restarts Home Assistant itself, all Add-on's remain running which could lead to some entities displaying an `Unknown` status. This status will update on the next change but for Alarm sensors that is not acceptable. A workaround to the problem is to Restart, or better yet, Refresh the `Comfort to MQTT` Add-on when Home Assistant restarts or when the configuration.yaml file is reloaded from `Developer tools` -> `YAML` -> `YAML configuration reloading`.

To automate this, you need to enable this hidden entity created by the `Home Assistant Supervisor`.

![image](https://github.com/djagerif/comfort2mqtt/assets/5621764/cedfc20a-3b38-405a-affe-e575c31057a0)

⚠️ This entity does not update in real-time, it takes around 2 minutes to change state.

Next you need to create an Automation that triggers on MQTT entry changes in the configuration.yaml file as per below.

To find your Add-on name for `service: hassio._restart` you can do a `ha ` query from the commandline interface and look for the `slug:` keyword or, after starting the Add-on, note the `Hostname` from the Add-on `Info` tab.

![image](https://github.com/djagerif/comfort2mqtt/assets/5621764/0b30bded-fe82-4c1d-a278-2c2789a4ef1f)

```
alias: Refresh Comfort to MQTT Add-on
description: >-
  When Home Assistant MQTT Configuration changes then refresh Comfort to MQTT entities.
trigger:
  - alias: When Reload 'ALL YAML CONFIGURATION' from Developer Tools
    platform: event
    event_type: call_service
    event_data:
      domain: mqtt
      service: reload
condition:
  - condition: state
    entity_id: binary_sensor.comfort_to_mqtt_running
    state: "on"
action:
  - service: notify.persistent_notification
    metadata: {}
    data:
      message: Home Assistant Add-on Refresh requested
      title: Comfort to MQTT Add-on
  - alias: Request a Refresh of all MQTT entities without a full Add-on reload
    service: mqtt.publish
    data:
      topic: comfort2mqtt/alarm/refresh
      payload: 000F8EC8 <- Provide your unique KEY value here. "Refresh Key:" can be found on startup in the Add-on log file. 
      qos: "2"
mode: single
```
⚠️ **Note:** When Comfort to MQTT starts up it will print the KEY value to be used for Refresh function authentication. Incorrect key values will be ignored.

`2024-06-12 17:45:27 INFO     Refresh Key: 000F8EC8`


## Home Assistant - 'Remote ARM Away' Automation (Optional)

Local arming Comfort to AWAY mode requires the Entry/Exit door to activate. There is however a way to arm to AWAY mode when the user is not at home, meaning in a Remote location. To arm Comfort without triggering the Entry/Exit door is possible via MQTT only.

If you want to trigger a Remote AWAY_ARM condition you can send the `REM_AWAY_ARM` string to the `comfort2mqtt/alarm/set` topic. Below is a quick Automation you can use to arm to REM_ARM_AWAY.

⚠️ **Note:** Never disarm your security system using insecure MQTT or other insecure connectivity methods. Make sure you use a trusted VPN to connect from the Internet and use MQTT encryption on your local network.

I've used an input_boolean as my test button below. Note that both the MQTT and native Alarm Control Panel methods are shown. The Alarm Control Panel method is shown as optional, without the ability to Remote Away Arm. They are disabled in the Automation.

```
alias: Alarm Arm Test
description: ""
triggers:
  - trigger: state
    entity_id:
      - input_boolean.test_button
    from: "off"
    to: "on"
conditions: []
actions:
  - action: mqtt.publish
    metadata: {}
    data:
      qos: 0
      topic: comfort2mqtt/alarm/set
      payload: REM_ARM_AWAY
    enabled: true
  - action: mqtt.publish
    metadata: {}
    data:
      topic: comfort2mqtt/alarm/set
      payload: ARM_CUSTOM_BYPASS
    enabled: true
  - action: alarm_control_panel.alarm_arm_away
    metadata: {}
    data: {}
    target:
      entity_id: alarm_control_panel.comfort_alarm
    enabled: false
  - action: alarm_control_panel.alarm_arm_custom_bypass
    metadata: {}
    data: {}
    target:
      entity_id: alarm_control_panel.comfort_alarm
    enabled: false
mode: single
```  


## Home Assistant - 'Battery Update' Automation (Optional)

The latest Comfort ARM-powered boards can report individual Battery/Charge and DC Supply voltages. Below is an automation you can use to query Comfort every minute for these values. You can safely extend the interval to 15 minutes or more as voltages don't usually change abruptly in a mostly-floating voltage device operation.

⚠️ **Note:** If you try this on a non-ARM powered mainboard then a warning message will be displayed in the Addon log as shown below.

`2024-08-08 19:05:22 WARNING  Unsupported MQTT Battery Update query received for ID: <UCMID>.`  
`2024-08-08 19:05:22 WARNING  Valid ID's: [0,1,33-39] with ARM-powered Comfort is required.`

Threshold values are internally defined as per below and will output a log message accordingly.

**Battery/Charge Voltage Levels:**

  voltage > 15:       # Critical Overcharge

  voltage > 14.6:     # Overcharge

  voltage <= 9.5:     # Battery Flat

  voltage < 11.5:     # Discharged

**DC Supply Voltage Levels:**

  voltage > 18:       # Criticaly High Voltage

  voltage > 17:       # High Voltage

  voltage <= 7:       # Criticaly Low Voltage or No Output

  voltage < 12:       # Low Voltage

When activating this automation on an ARM mainboard then the following two responses are received from Comfort. The first is for Battery/Charge voltage and the second for the DC Supply voltage expressed as an 8-bit value. The formulas for voltage calculation, using the examples below, are:

⚠️ **Note:** Battery voltages change when AC is connected or not. When AC is connected you will see the Charge voltage. When disconnected, it will be the battery voltage. Due to component tolerances, the values might not be exactly what is measured with a precision test instrument.

```
Battery/Charge Voltage = 209/255 * (3.3/2.7) * 12.7 - 0.35 = 12.37V (AC Disconnected)
DC Supply Voltage = 0/255 * (3.3/2.7) * 14.9 = 0V

2025-02-16 10:54:58 DEBUG    D?0101D1
2025-02-16 10:54:58 DEBUG    D?010200
```

```
Battery/Charge Voltage = 233/255 * (3.3/2.7) * 12.7 - 0.75 = 13.43V (AC Connected)
DC Supply Voltage = 209/255 * (3.3/2.7) * 14.9 = 14.96V

2025-02-16 10:55:58 DEBUG    D?0101E9
2025-02-16 10:55:58 DEBUG    D?0102D1
```

Take note of the `condition` block below, this is your Comfort II ULTRA device and is used as a check to make sure the LAN connection to Comfort is in a Connected and Logged-In state.

![image](https://github.com/user-attachments/assets/c387efcc-89a0-4af2-9c66-0ea36a8e5e72)

```
alias: Comfort Battery Update Query (Mainboard)
description: Query an ARM powered Comfort Mainboard Battery and DC Supply voltages.
trigger:
  - platform: time_pattern
    seconds: "0"
    enabled: true
condition:
  - type: is_connected
    condition: device
    device_id: 2c67370b6618f7cb8059cb278f23e613
    entity_id: c69f4645a0654166aac672f675c0aafa
    domain: binary_sensor
action:
  - data:
      qos: "2"
      topic: comfort2mqtt/alarm/battery_update
      payload: "1"
    action: mqtt.publish
mode: single
```
⚠️ **Note:** For supported ARM-based firmware you can change the 'payload' data from e.g. "1" to "0" for a bulk update of all voltages. It does however require a new Comfort ARM firmware which is currently still in development.

## Hardware and Interface support

This Add-on was specifically developed for the Comfort II ULTRA range of Alarm Systems with File System type `34`. Comfort II ULTRA firmware as tested is `7.201`. If any other Comfort system, model or firmware lower than `7.201`, is used then results may be unexpected.

The following Cytech Universal Communications Modules (UCM) Ethernet modules are supported:

* [UCM/Eth01] - Obsolete/Untested

* [UCM/Eth02] - Obsolete/Untested

* [UCM/Wifi01] - Not Recommended (WiFi) - Firmware 7.176 or later.

* [UCM/Eth03 or Eth03 Mainboard Plug-in] - Recommended (LAN) - Firmware 7.176 or later.

This software _requires_ a fully functional Comfort Ethernet or Wifi configuration with inactivity timeout set to the default value of 2 minutes. The UCM/Wifi is not recommended due to possible connectivity issues that could arise from switching between different AP's or other possible sources of RF noise. For best performance it is recommended to use either the UCM/Eth03 or the onboard Eth03 Plug-in module on the newer CM9001 Comfort Ultra models. Use a good quality CAT5e or better cable between Comfort and your network device.

If your network is segmented using a firewall, or any other similar device, you must ensure all applicable ports are allowed between Home Assistant and Comfort. The default port for the UCM/Eth03 is TCP/1002 which is Port #2 of a UCMEth03.
  
⚠️ The UCM/WiFi uses port TCP/3000 as the default port. Any port may be used as long as there are no overlaps with existing services on the network.

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

### Option: `MQTT Transport Encryption` (Optional)

  Use TLS Encryption for MQTT Transport (Default False).

### Option: `CA Certificate File` (Optional)

  A file containing a CA certificate. Place this file in the Home Assistant `addon_configs/<comfort2mqtt slug>/certificates` folder.
  
### Option: `Require Certificate Authentication` (Optional)
  
  If enabled, authentication will be enabled using the mandatory Client Certificate and Client Key file options.

### Option: `Client Certificate File` (Optional)

  A file containing a Client Certificate, including its chain. Place this file in the Home Assistant `addon_configs/<comfort2mqtt slug>/certificates` folder.

### Option: `Client Private Key File` (Optional)

  A file containing the Client Private key. Place this file in the Home Assistant `addon_configs/<comfort2mqtt slug>/certificates` folder.

### Option: `Comfort TCP Port` (Optional)

  The Comfort UCM/Eth03 TCP port used for connectivity. UCM/ETh03 can be changed so please check your Comfort configuration and use the port that is configured for access. Note that only one client can connect to any given TCP port. The default is '1002'

### Option: `Comfort system IP address`

  The Comfort UCM/Eth03 IP address or Hostname used for connectivity.

### Option: `Comfort User Login ID`

  Cytech Comfort User Login ID with the appropriate rights. Login ID has minimum 4 and a maximum of 6 characters. For full functionality you need at least Local Arm/Disarm and Remote Arm/Disarm capabilities on Comfort. See the [Comfigurator Programming Guide][progman], `Security Settings` and `Sign-in Codes` sections for more information on user creation and rights.

  [progman]: http://www.cytech.biz/download_files.php?item_id=1082

### Option: `Comfort Configuration file` (Optional)

  Comfort Configuration file, also referred to as the 'CCLX' file to be used for object enrichment EG. Zone Names etc. Place this file in the Home Assistant `addon_configs/<comfort2mqtt slug>` folder. If no file is specified then the default `comfigurator.cclx` will be used.

  To upload a file to the `addon_configs` directory you could use something like [Samba share][samba] Add-on or similar allowing filesystem access to selected directories on Home Assistant.

  ⚠️ **Note:** The CCLX filename cannot contain spaces.

  [samba]:https://github.com/home-assistant/addons/tree/master/samba
      
### Option: `Global Log Verbosity` (Optional)

  This option controls the level of log output by the Add-on and can be changed to be more or less verbose, which might be useful when you are dealing with an unknown issue. Possible values are:

- `DEBUG`:   Shows detailed debug information.
- `ERROR`:   Runtime errors that do not require immediate action.
- `WARNING`: Exceptional occurrences that are not errors.
- `INFO`:    Normal, usually, interesting events (`DEFAULT`).

  Please note that each level automatically includes log messages from a more severe level, e.g. `DEBUG` also shows `INFO` messages. By default, the `log_level` is set to `INFO`, which is the recommended setting unless you are troubleshooting.

### Option: `Comfort Zone Inputs` (Optional)

  Select number of Published Comfort Inputs/Zones starting from Zone 1. Published Zones is a single contiguous block from 1 to <Value>. Default 8, Max. 96

### Option: `Comfort Zone Outputs` (Optional)

  Select number of Published Comfort Outputs starting from Output 1. Published Outputs is a single contiguous block from 1 to <Value>. Default 0, Max. 96

### Option: `Comfort SCS/RIO Inputs` (Optional)

  Set number of Published SCS/RIO Inputs. Published SCS/RIO Inputs is a single contiguous block from 1 to <Value>. Default 0, Max. 120. 

### Option: `Comfort SCS/RIO Outputs` (Optional)

  Set number of Published SCS/RIO Outputs. Published SCS/RIO Outputs is a single contiguous block from 1 to <Value>. Default 0, Max. 120. 

### Option: `Comfort Responses` (Optional)

  This sets the number of Responses that the Add-on subscribes to. Valid range values are from 0 - 1024. If you subscribe to the first 100 responses and trigger a response number EG. 200, then it will not be sent to Comfort for execution. Only subscribed responses are executed. The Default value is `0`.

### Option: `Comfort MQTT Bridge Battery Update Target ID` (Optional)

  This sets the ID to be queried by the `Battery Update` Bridge Control button. Valid range values are [0,1,33 - 39]. The Default value is `1`. `0` is used on a yet to be released ARM firmware that queries all batteries and chargers so you can monitor all of them with a single query.

### Option: `Set Comfort Time and Date` (Optional)

  Set Comfort Time and Date when the Add-on logs in and automatically every day at midnight. The default value is `False`.


## Support

Got questions?

- The [Comfort Forums][comfortforums] for any questions or suggestions


## Authors & Contributors

The original source for this project was done by [koocyrat][koochyrat]. This project is a modified, and slightly extended version, of the same source project and adapted to a native Home Assistant Add-on. Among several posts, various Comfort forum members also had good suggestions which, in part, contributed to this project as inspiration.

## Disclaimer

Not being a fulltime programmer, but rather just a tinkerer, I try and keep things working but changes to Comfort firmware and features might not always work with this Add-on. I will try and update this Add-on as time and skill allow. A full disclaimer of warranty is included in the Apache licence terms and conditions for use below.


## License

```
Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

    1. Definitions.

        "License" shall mean the terms and conditions for use, reproduction, and distribution as defined by Sections 1 through 9 of this document.

        "Licensor" shall mean the copyright owner or entity authorized by the copyright owner that is granting the License.

        "Legal Entity" shall mean the union of the acting entity and all other entities that control, are controlled by, or are under common control with that entity. For the purposes of this definition, "control" means (i) the power, direct or indirect, to cause the direction or management of such entity, whether by contract or otherwise, or (ii) ownership of fifty percent (50%) or more of the outstanding shares, or (iii) beneficial ownership of such entity.

        "You" (or "Your") shall mean an individual or Legal Entity exercising permissions granted by this License.

        "Source" form shall mean the preferred form for making modifications, including but not limited to software source code, documentation source, and configuration files.

        "Object" form shall mean any form resulting from mechanical transformation or translation of a Source form, including but not limited to compiled object code, generated documentation, and conversions to other media types.

        "Work" shall mean the work of authorship, whether in Source or Object form, made available under the License, as indicated by a copyright notice that is included in or attached to the work (an example is provided in the Appendix below).

        "Derivative Works" shall mean any work, whether in Source or Object form, that is based on (or derived from) the Work and for which the editorial revisions, annotations, elaborations, or other modifications represent, as a whole, an original work of authorship. For the purposes of this License, Derivative Works shall not include works that remain separable from, or merely link (or bind by name) to the interfaces of, the Work and Derivative Works thereof.

        "Contribution" shall mean any work of authorship, including the original version of the Work and any modifications or additions to that Work or Derivative Works thereof, that is intentionally submitted to Licensor for inclusion in the Work by the copyright owner or by an individual or Legal Entity authorized to submit on behalf of the copyright owner. For the purposes of this definition, "submitted" means any form of electronic, verbal, or written communication sent to the Licensor or its representatives, including but not limited to communication on electronic mailing lists, source code control systems, and issue tracking systems that are managed by, or on behalf of, the Licensor for the purpose of discussing and improving the Work, but excluding communication that is conspicuously marked or otherwise designated in writing by the copyright owner as "Not a Contribution."

        "Contributor" shall mean Licensor and any individual or Legal Entity on behalf of whom a Contribution has been received by Licensor and subsequently incorporated within the Work.
    2. Grant of Copyright License. Subject to the terms and conditions of this License, each Contributor hereby grants to You a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable copyright license to reproduce, prepare Derivative Works of, publicly display, publicly perform, sublicense, and distribute the Work and such Derivative Works in Source or Object form.
    3. Grant of Patent License. Subject to the terms and conditions of this License, each Contributor hereby grants to You a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable (except as stated in this section) patent license to make, have made, use, offer to sell, sell, import, and otherwise transfer the Work, where such license applies only to those patent claims licensable by such Contributor that are necessarily infringed by their Contribution(s) alone or by combination of their Contribution(s) with the Work to which such Contribution(s) was submitted. If You institute patent litigation against any entity (including a cross-claim or counterclaim in a lawsuit) alleging that the Work or a Contribution incorporated within the Work constitutes direct or contributory patent infringement, then any patent licenses granted to You under this License for that Work shall terminate as of the date such litigation is filed.
    4. Redistribution. You may reproduce and distribute copies of the Work or Derivative Works thereof in any medium, with or without modifications, and in Source or Object form, provided that You meet the following conditions:
        (a) You must give any other recipients of the Work or Derivative Works a copy of this License; and
        (b) You must cause any modified files to carry prominent notices stating that You changed the files; and
        (c) You must retain, in the Source form of any Derivative Works that You distribute, all copyright, patent, trademark, and attribution notices from the Source form of the Work, excluding those notices that do not pertain to any part of the Derivative Works; and
        (d) If the Work includes a "NOTICE" text file as part of its distribution, then any Derivative Works that You distribute must include a readable copy of the attribution notices contained within such NOTICE file, excluding those notices that do not pertain to any part of the Derivative Works, in at least one of the following places: within a NOTICE text file distributed as part of the Derivative Works; within the Source form or documentation, if provided along with the Derivative Works; or, within a display generated by the Derivative Works, if and wherever such third-party notices normally appear. The contents of the NOTICE file are for informational purposes only and do not modify the License. You may add Your own attribution notices within Derivative Works that You distribute, alongside or as an addendum to the NOTICE text from the Work, provided that such additional attribution notices cannot be construed as modifying the License.

    You may add Your own copyright statement to Your modifications and may provide additional or different license terms and conditions for use, reproduction, or distribution of Your modifications, or for any such Derivative Works as a whole, provided Your use, reproduction, and distribution of the Work otherwise complies with the conditions stated in this License.
    5. Submission of Contributions. Unless You explicitly state otherwise, any Contribution intentionally submitted for inclusion in the Work by You to the Licensor shall be under the terms and conditions of this License, without any additional terms or conditions. Notwithstanding the above, nothing herein shall supersede or modify the terms of any separate license agreement you may have executed with Licensor regarding such Contributions.
    6. Trademarks. This License does not grant permission to use the trade names, trademarks, service marks, or product names of the Licensor, except as required for reasonable and customary use in describing the origin of the Work and reproducing the content of the NOTICE file.
    7. Disclaimer of Warranty. Unless required by applicable law or agreed to in writing, Licensor provides the Work (and each Contributor provides its Contributions) on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied, including, without limitation, any warranties or conditions of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A PARTICULAR PURPOSE. You are solely responsible for determining the appropriateness of using or redistributing the Work and assume any risks associated with Your exercise of permissions under this License.
    8. Limitation of Liability. In no event and under no legal theory, whether in tort (including negligence), contract, or otherwise, unless required by applicable law (such as deliberate and grossly negligent acts) or agreed to in writing, shall any Contributor be liable to You for damages, including any direct, indirect, special, incidental, or consequential damages of any character arising as a result of this License or out of the use or inability to use the Work (including but not limited to damages for loss of goodwill, work stoppage, computer failure or malfunction, or any and all other commercial damages or losses), even if such Contributor has been advised of the possibility of such damages.
    9. Accepting Warranty or Additional Liability. While redistributing the Work or Derivative Works thereof, You may choose to offer, and charge a fee for, acceptance of support, warranty, indemnity, or other liability obligations and/or rights consistent with this License. However, in accepting such obligations, You may act only on Your own behalf and on Your sole responsibility, not on behalf of any other Contributor, and only if You agree to indemnify, defend, and hold each Contributor harmless for any liability incurred by, or claims asserted against, such Contributor by reason of your accepting any such warranty or additional liability.

END OF TERMS AND CONDITIONS
```

More details can be obtained from [apache.org][license].

[license]: https://www.apache.org/licenses/LICENSE-2.0
[comfort2mqtt]: https://github.com/djagerif/comfort2mqtt
[koochyrat]: https://github.com/koochyrat/comfort2
[comfortforums]: https://comfortforums.com/
