# Change Log
All notable changes to this project will be documented in this file.


## [1.2.0]

## To Do ##
 - Test Client/Server Authentication certificates
 - Look into ARM CPU and Battery/DC Polling if detected. D?. Note: u?01 not supported on old CM-9000. CM-9001 + ARM/Toshiba for D? to work.
 - Clear Battery values when CPU is set to <default/PIC>, Set to '-1'. Run Update. Should not be an issue as value does not change dynamically.
 - Add a Battery Status function. Ok, Warning, Critical.
 - Cleanup if no CCLX file is availabel EG. Device Name.
 
    
### Added
 - Added reporting for more Comfort models when detected.
 - Check for new ARM or Toshiba Mainboard CPU.
 
 

### Changed
 - Update all references of Comfort II Ultra to Comfort to be more inclusive of other Comfort system models.
 - Remove unique identifer for Comfort identification, makes it easier to read/identify.
 - Remove attributes from Diagnostic entities.

### Fixed
 - Initial startup Diagnostics values 'Unknown'. Data is now correctly populated on startup.


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
 
