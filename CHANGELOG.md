## [1.3.0] - New RC test release

### Todo ###

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
 
