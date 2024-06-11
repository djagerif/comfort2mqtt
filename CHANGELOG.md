# Change Log
All notable changes to this project will be documented in this file.

## [1.0.4] - Unreleased

## To Do ##
 - Test Client/Server certificates
 - Change Counters (State/Value), Inputs(State/Bypass) and Outputs to JSON format. Incl time, desc, bypass + state. Done.
 - Try port busy error or warning on Comfort. Done
 - Fix IP > 128 to exclude BypassCache. Crash with keyError. Done
 - Add description file for outputs. Use combined file, update file to include type. Done, using CCLX file.
 - Limit BY to <= 128. Done.
 - Add optional descriptions for Flags, Counters, Sensors, Timers. Done.
 - Check QoS on sent 'SET' commands. Done
 - Add JSON format to ALARM. Include Type,Ver,FS,MPU and SN.
 - Add file name to options.

### Added
 - Improve MQTT server shutdown.
 - MQTT Broker Encryption.
 

### Changed
 - Increased "zones.csv" permitted size to 20KB. Included Input and Output names. Max. Names = 30 characters.
 - Changed object reporting to JSON format for Zones, Outputs and Counters.

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
 
