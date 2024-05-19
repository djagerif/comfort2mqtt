# Change Log
All notable changes to this project will be documented in this file.
 
### Testing ###

## Unreleased ##
## [1.0.2] ## 
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
 
