## [1.6.1] - Busy...

### Added
 
### Changed
 - Update Copyright date.
 - MQTT Login Message, removed 'Comfort' string.
 - Possible removal of i386, armhf and armv7 bases.

### Fixed
 

## [1.6.0] - 2025-10-11

### Added
 - LR Login Reports. Logs Login Reports from Local/Remote Phones, Keypads and UCM's.
 
### Changed
 - Change object_id to default_entity_id.

### Fixed
 - Incomplete object_id's. Correctly set default_entity_id properties for system created objects.

## [1.5.1] - 2025-08-22

### Added
 
### Changed
- Update DOCS.md and add MQTT entity `object-id` to simplify Comfort object identification.
- Reclasify some ERROR messages to DEBUG status.
- Update RP and DB command responses and checks. DB now reports which Doorbell was pressed.
- Changed 'Door Bell' to 'Doorbell'.

### Fixed
- Keepalive timeout setting not set under certain error conditions.


## [1.5.0] - 2025-05-25

### Added
 - Update DOCS.md to add explanation of Alarm Control Panel UI configuration options.
 - Updated DOCS.md to clarify `LAN Connected` state.
 - Updated Battery Voltage calculation.
 
### Changed
- Clarify D?nn01 voltage UI definition for `Battery Voltage` renamed to `Battery/Charge Voltage`. This is the Battery/Charge Test Point voltage measured at the +12V/COM terminals adding average component voltage losses to indicate approximate battery voltage.
- Clarify D?nn02 voltage UI definition for `Charger Voltage` renamed to `DC Supply Voltage`. This is the 12V DC Output circuit Test Point voltage measured after the external PSU control circuit.
- Update random MQTT client ID generator.
- Minor syntax changes.
- Reworked TCP and Application Keepalives. Now correctly indicates LAN status.

*Note: Possible breaking change for CM-9001 ARM based boards only.
- Update `Battery Status` UI definition to `Battery/Charger Status`.
- Update `Charger Status` UI definition to `DC Supply Status`.
*Go to Settings -> Devices and services. Select MQTT and click on 'Devices. Click on `Comfort II ULTRA` and under `Device Info` select the three dots (...) which give the option to Download Diagnostics or Delete. Click on Delete. Now go back and restart the Addon from the Settings/Addon screen menu.


### Fixed
 - a? Low Battery decode referenced incorrect index.
 


## [1.4.3] - 2025-01-26

### Added

### Changed
 - Updated DOCS.MD to specify supported Home Assistant OS only. Container and Core are not supported.

### Fixed
 - Fixed AM log messages.
 - Workaround for unsupported firmware where the b? command is not available, start the BypassZone cache with all '0's.
 - Remove extraneous " character from filename path.


## [1.4.2] - 2025-01-22

### Added

### Changed
 - Update LOG messages for Zones to be the same as the Alarm Message format.
 - Update DOCS.md on specifying the CCLX filename format to be used for enrichment.

### Fixed
 - Fix a? exception when Comfort is powered on without a battery or Low battery is detected.


## [1.4.1] - 2025-01-07
 
### Added
 - Additional input validation checks.
 - Additional checks for valid certificate file.
 - `Alarm Message` UI enhancements when CCLX file is loaded.

### Changed
 - Moved to defusedxml for cclx file parsing.
 - Added 5s timeout to internal Home Assistant http connection.
 - Updated DOCS.

### Fixed  


## [1.4.0] - 2024-12-27
 
### Added
 - Configurable Battery Update ID via UI. Select which component is updated when pressing the 'Battery Update' control. [0,1,33,34..39]. Default 1 (Mainboard).
 - Add Remote Arm Away mode via MQTT. Send 'REM_ARM_AWAY' to /comfort2mqtt/alarm/set. Does not require entry/exit activation.

### Changed

### Fixed


## [1.3.1] - 2024-12-21
 
### Added

### Changed
 - Do not query SCS/RIO Inputs/Outputs and Responses if set to 0 in the configuration.

### Fixed
 - Startup exception that can happen without a cclx file uploaded. Swapped V? and u?01 queries to correctly populate internal structure.


## [1.3.0] - 2024-12-17

### Added
 - Added D?0000 for future ARM processor firmware.
 - Add "Unsupported Firmware" message to log if detected.

### Changed
 - Using Alpine Linux 3.21.0 as the Home Assistant base image has been upgraded.
 - Optimise MQTT Main topic for improved speed. Split Battery and Charger information to seperate topic.
 - Expanded on Battery Check Home Assistant Automation. Allowing '0' for bulk updates with improved logging messages.

### Fixed
- Updated ARM Charger Threshold levels according to Cytech requirements.


## [1.2.6] - 2024-12-15

### Added
 
### Changed
 - Updated ARM Battery Status voltage levels according to Cytech requirements.

### Fixed
 

## [1.2.5] - 2024-12-14

### Added
 
### Changed
 - Added "Unknown" state when receiving undocumented S? status request return values other than 0-3.

### Fixed
 - Updated documentation to reflect correct "addon_configs" directory.
 - Fixed MQTT Battery Update automation handling.


## [1.2.3] - 2024-09-02

### Added
 - Added Homeassistant Alpine Linux Docker release version to Bridge attributes.
 
### Changed
 - MQTT Bridge Status unique ID, Object ID and Name change to be more descriptive.

### Fixed


## [1.2.2] - 2024-08-20

### Added
 
### Changed
 - Changed Counters, Sensors, Inputs and Outputs to be No-Retain. HA will request update once connected.
 - Limit O! values to [0 - 4] only.

### Fixed


## [1.2.1] - 2024-08-17

### Added
 - Add Alarm Mode integer values 0 - 4. See MD or M? Comfort documentation.
    1 = Away Mode
    2 = Night Mode
    3 = Day Mode
    4 = Vacation Mode
 
### Changed
 - Update UniqueID for Comfort Filesystem. (Breaking)
 
### Fixed
 - Enable Comfort MQTT main attributes Retain flag.


## [1.2.0] - 2024-08-10

### Added
 - Added reporting for more Comfort models when detected.
 - For Future Comfort Enhancement: Check for new ARM or Toshiba Mainboard CPU. When ARM/Toshiba detected, use D?00xx as keepalives.
   Note: D?00xx command is only suggested as a feature request to Cytech and might not go into Production.
 - Add a Battery Status function. Critical[<12.23, >14.4], Warning[<12.58, >14.2], Ok[>=12.58, <=14.2].
 - Add MQTT Battery/Charger query with parameter of 1,33-35[7] for Main + Slaves. Send decimal value in MQTT query.
 
### Changed
 - Update all references of Comfort II Ultra to Comfort to be more inclusive of other Comfort system models.
 - Remove unique identifer for Comfort identification, makes it easier to read/identify.
 - Remove attributes from Diagnostic entities.
 - Split Comfort to MQTT Bridge and Comfort II ULTRA device under MQTT.
 - Removed u?00 from polling as this seems to create issues with subsequent commands.
 - Domain changed from 'comfort2' to 'comfort2mqtt'.

### Fixed
 - Initial startup Diagnostic values 'Unknown'. Data is now correctly populated on startup.


## [1.1.1] - 2024-06-30
 
### Added
 - Add Comfort MQTT Device Properties to domain 'comfort2'.
 - Added MQTT Auto Discovery once Comfort is connected. Only System Sensors created.
 - Range out-of-bounds checking for Zones, Outputs and Responses. 
 
### Changed
 - Updated 'SN' decoding.
 - Update Alarm States when arming. Changed from `Pending` to `Arming` as per documentation.
 - BypassZones changed from `-1` to `0` when no zones are bypassed. <BREAKING!!>
 
### Fixed
 - Only report CCLX Zone information missing if object is inside configured object range. Inputs, Outputs etc.
 - Fix 'broker-ca' filename not imported correctly.


## [1.1.0] - 2024-06-15
 
### Added
 - Improve MQTT server shutdown on exit.
 - MQTT Broker Encryption.
 - Add user configurable Comfort CCLX file option to be used for enrichment EG. Zone Names or Descriptions.
 - Add 'refresh' + 'key' to publish all MQTT values without restart.
 - Added Integer Check for 'set' commands where required.
 - Added default "ca.crt" to ca certificate option.
 - Reintroduced random mqtt client-id to prevent duplicates.

### Changed (Breaking)
 - No longer using 'zones.csv' file, replaced by comfigurator CCLX file.
 - Changed object reporting to JSON format for Zone Inputs, Outputs, Counters, Sensors and Flags.
 - Removed Timers

### Fixed


## [1.0.3] - 2024-06-01

### Added

### Changed
 - Optimised Comfort Keepalives, added update to all Comfort Send commands.

### Fixed


## [1.0.2] - 2024-05-24
Minor bug-fix release.

### Added
 - Add 10mS delay between bulk publish commands on startup or reconnect. (Z?, z?, Y?, y?, f?00, r?00, r?01)
 - Add 10mS for Comfort commands before next one is sent.

### Changed
 - Updated Automation to restart Add-on for MQTT configuration reload.
 - removed random mqtt-client id generation. Client-ID is now just 'comfort2mqtt'
 - 3s delay on MQTT connect reduced to 1s

### Fixed
 - Alarm triggered state incorrectly set.
 - Prevent Zone Trouble state (2) from activating Zone Input.


## [1.0.1] - 2024-05-05
  
### Added
 
### Changed
  
### Fixed
 - Sanity Check improved for invalid data received from Comfort.
 - Fixed MQTT WebSockets connection.


## [1.0.0] - 2024-05-04
Initial release of Comfort to MQTT for Home Assistant.
 
### Added
 
### Changed
  
### Fixed
 
