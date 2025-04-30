# Copyright(c) 2018 Khor Chin Heong (koochyrat@gmail.com) for original project code and additional 
# copyright(c) 2025 Ingo de Jager (ingodejager@gmail.com) for modifications done 
# to the original project sources contained in this project.
#
# Modified by Ingo de Jager 2025 (ingodejager@gmail.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Notes:
#
#
import defusedxml.ElementTree as ET
import ssl
from OpenSSL import crypto
import os
import requests
import json
from pathlib import Path
import re
import signal
import ipaddress
import socket
import time
import datetime
import threading
import logging
from datetime import datetime, timedelta
import secrets
import paho.mqtt.client as mqtt
from argparse import ArgumentParser

DOMAIN = "comfort2mqtt"
ADDON_SLUG = ''
ADDON_VERSION = "N/A"
COMFORT_SERIAL = "00000000"       # Default Serial Number.
COMFORT_KEY = "00000000"          # Default Refresh Key.

SupportedFirmware = float(7.201)  # Minimum Supported firmware.

MAX_ZONES = 96                    # Configurable for future expansion
MAX_OUTPUTS = 96                  # Configurable for future expansion
MAX_RESPONSES = 1024              # Configurable for future expansion

lower = 268435456
upper = 4294967295
rand_int = lower + secrets.randbelow(upper - lower + 1)
rand_hex_str = hex(rand_int)
mqtt_client_id = DOMAIN+"-"+str(rand_hex_str[2:])       # Generate pseudo random client-id each time it starts.

REFRESHTOPIC = DOMAIN+"/alarm/refresh"                  # Use this topic to refresh objects. Not a full Reload but request Update-All from Addon. Use 'key' for auth.
BATTERYREFRESHTOPIC = DOMAIN+"/alarm/battery_update"    # Used to request Battery and DC Supply voltage updates. To be used by HA Automation for periodic polling.
BATTERYSTATUSTOPIC = DOMAIN+"/alarm/battery_status"     # List of Battery and DC Supply Output Status.

ALARMSTATETOPIC = DOMAIN+"/alarm"
ALARMSTATUSTOPIC = DOMAIN+"/alarm/status"
ALARMBYPASSTOPIC = DOMAIN+"/alarm/bypass"               # List of Bypassed Zones.
ALARMCONNECTEDTOPIC = DOMAIN+"/alarm/connected"
ALARMMODETOPIC = DOMAIN+"/alarm/mode"                   # Integer value of current Mode. See M? and MD.

ALARMCOMMANDTOPIC = DOMAIN+"/alarm/set"
ALARMAVAILABLETOPIC = DOMAIN+"/alarm/online"
ALARMLWTTOPIC = DOMAIN+"/alarm/LWT"
ALARMMESSAGETOPIC = DOMAIN+"/alarm/message"
ALARMTIMERTOPIC = DOMAIN+"/alarm/timer"
ALARMDOORBELLTOPIC = DOMAIN+"/alarm/doorbell"

FIRST_LOGIN = False         # Don't scan Comfort until MQTT connection is made.
RUN = True
BYPASSEDZONES = []          # Global list of Bypassed Zones
BROKERCONNECTED = False     # MQTT Broker Status
COMFORTCONNECTED = False    # Comfort LAN connection Status
ZONEMAPFILE = False         # CCLX file present or not.
SCSRIOMAPFILE = False
OUTPUTMAPFILE = False
COUNTERMAPFILE = False
SENSORMAPFILE = False
FLAGMAPFILE = False
DEVICEMAPFILE = False
USERMAPFILE = False
device_properties = {}
file_exists  = False
ACFail = False              # Indicates ACFail status.

device_properties['CPUType'] = "N/A"
device_properties['Version'] = "N/A"
device_properties['BatteryVoltageMain'] = "-1"
device_properties['BatteryVoltageSlave1'] = "-1"
device_properties['BatteryVoltageSlave2'] = "-1"
device_properties['BatteryVoltageSlave3'] = "-1"
device_properties['BatteryVoltageSlave4'] = "-1"
device_properties['BatteryVoltageSlave5'] = "-1"
device_properties['BatteryVoltageSlave6'] = "-1"    # Experimental
device_properties['BatteryVoltageSlave7'] = "-1"    # Experimental
device_properties['ChargeVoltageMain'] = "-1"
device_properties['ChargeVoltageSlave1'] = "-1"
device_properties['ChargeVoltageSlave2'] = "-1"
device_properties['ChargeVoltageSlave3'] = "-1"
device_properties['ChargeVoltageSlave4'] = "-1"
device_properties['ChargeVoltageSlave5'] = "-1"
device_properties['ChargeVoltageSlave6'] = "-1"    # Experimental
device_properties['ChargeVoltageSlave7'] = "-1"    # Experimental
device_properties['ComfortHardwareModel'] = "CM9000-ULT"
device_properties['sem_id'] = 0
device_properties['SerialNumber'] = "00000000"
device_properties['BatteryStatus'] = "N/A"
device_properties['ChargerStatus'] = "N/A"
device_properties['BridgeConnected'] = 0
device_properties['CustomerName'] = None
device_properties['Reference'] = None
device_properties['Version'] = None
device_properties['ComfortFileSystem'] = None
device_properties['ComfortFirmwareType'] = None

# Comfort FileSystem values and Model Numbers
models = {34: "Comfort II ULTRA",
          31: "Comfort II Optimum",
          36: "Logic Engine",
          37: "EMS",
          38: "EMS2",
          39: "KS",
          35: "CM9001-EX",
          30: "Comfort II SPC",
          18: "Comfort I PRO (Obsolete)",
          17: "Comfort I ENTRY (Obsolete)",
          24: "Comfort I ULTRA (Obsolete)"
        }

# Includes possible future expansion to 7 Slaves.
BatterySlaveIDs = {1:"BatteryVoltageMain",
          33:"BatteryVoltageSlave1",
          34:"BatteryVoltageSlave2",
          35:"BatteryVoltageSlave3",
          36:"BatteryVoltageSlave4",
          37:"BatteryVoltageSlave5",
          38:"BatteryVoltageSlave6",
          39:"BatteryVoltageSlave7"
}
ChargerSlaveIDs = {1:"ChargeVoltageMain",
          33:"ChargeVoltageSlave1",
          34:"ChargeVoltageSlave2",
          35:"ChargeVoltageSlave3",
          36:"ChargeVoltageSlave4",
          37:"ChargeVoltageSlave5",
          38:"ChargeVoltageSlave6",
          39:"ChargeVoltageSlave7"

}

BatteryVoltageNameList = {0:"BatteryVoltageMain",
                      1:"BatteryVoltageSlave1",
                      2:"BatteryVoltageSlave2",
                      3:"BatteryVoltageSlave3",
                      4:"BatteryVoltageSlave4",
                      5:"BatteryVoltageSlave5",
                      6:"BatteryVoltageSlave6",
                      7:"BatteryVoltageSlave7"
}
ChargerVoltageNameList = {0:"ChargeVoltageMain",
                      1:"ChargeVoltageSlave1",
                      2:"ChargeVoltageSlave2",
                      3:"ChargeVoltageSlave3",
                      4:"ChargeVoltageSlave4",
                      5:"ChargeVoltageSlave5",
                      6:"ChargeVoltageSlave6",
                      7:"ChargeVoltageSlave7"
}

BatteryVoltageList = {0:"-1",
                      1:"-1",
                      2:"-1",
                      3:"-1",
                      4:"-1",
                      5:"-1",
                      6:"-1",
                      7:"-1"
}
ChargerVoltageList = {0:"-1",
                      1:"-1",
                      2:"-1",
                      3:"-1",
                      4:"-1",
                      5:"-1",
                      6:"-1",
                      7:"-1"
}

ZoneCache = {}              # Zone Cache dictionary.
#BypassCache = {}            # Zone Bypass Cache dictionary.
BypassCache = {i: 0 for i in range(1,MAX_ZONES + 1)}   # generate empty bypass cache for all zones. (Up to MAX_ZONES)
CacheState = False          # Initial Cache state. False when not in sync with Bypass Zones (b?). True, when in Sync.

logger = logging.getLogger(__name__)

def boolean_string(s):

    if s.lower() == 'true':
        return True
    #elif s.lower() == 'false':
    #    return False
    else:
        #raise ValueError("Not a valid boolean string. Set to either 'True' or 'False'.")
        return False
    
parser = ArgumentParser()

group = parser.add_argument_group('MQTT options')
group.add_argument(
    '--broker-address',
    required=True,
    help='IP Address of the MQTT broker')

group.add_argument(
    '--broker-port',
    type=int, default=1883,
    help="TCP Port Number to connect to the MQTT broker. [default: '1883']")

group.add_argument(
    '--broker-username',
    required=True,
    help='MQTT Username to use for MQTT broker authentication.')

group.add_argument(
    '--broker-password',
    required=True,
    help='MQTT Password to use for MQTT broker authentication.')

group.add_argument(
    '--broker-protocol',
    required=False,
    dest='broker_protocol', default='TCP', choices=(
         'TCP', 'WebSockets'),
    help="TCP or WebSockets Transport Protocol for MQTT broker. [default: 'TCP']")

group.add_argument(
    '--broker-encryption',
    type=boolean_string, default='false',
    help="Use MQTT TLS encryption, 'True'|'False'. [default: 'False']")

group.add_argument(
    '--broker-ca',
    help='Filename of CA certificate to trust.')
group.add_argument(
    '--broker-client-cert',
    help='Filename of PEM-encoded client certificate (public part). If not '
         'specified, client authentication will not be used. Must also '
         'supply the private key (--broker-client-key).')

group.add_argument(
    '--broker-client-key',
    help='Filename of PEM-encoded client key (private part). If not '
         'specified, client authentication will not be used. Must also '
         'supply the public key (--broker-client-cert). If this file is encrypted, Python '
         'will prompt for the password at the command-line.')

group = parser.add_argument_group('Comfort System options')
group.add_argument(
    '--comfort-address',
    required=True,
    help='IP Address of the Comfort system in IPV4 format.')

group.add_argument(
    '--comfort-port',
    type=int, default=1002,
    help="TCP Port to connect to Comfort system. [default: '1002']")

group.add_argument(
    '--comfort-login-id',
    required=True,
    help='Comfort system Login ID.')

group.add_argument(
    '--comfort-cclx-file',
    help='Comfort (CCLX) Configuration filename.')

group.add_argument(
    '--comfort-battery-update',
    type=int, default=1,
    help="Comfort MQTT Bridge 'Battery Update' query ID. [default: '1']")

group.add_argument(
    '--comfort-time',
    type=boolean_string, default='false',
    help="Set Comfort Date and Time flag, 'True'|'False'. [default: 'False']")

group = parser.add_argument_group('Comfort Alarm options')
group.add_argument(
    '--alarm-inputs',
    type=int, default=8,
    help="Number of physical Zone Inputs, values from 8 - " + str(MAX_ZONES) + " in increments of 8. [default: '8']")

group.add_argument(
    '--alarm-outputs',
    type=int, default=0,
    help="Number of physical Zone Outputs, values from 0 - " + str(MAX_OUTPUTS) + " in increments of 8. [default: '0']")

group.add_argument(
    '--alarm-responses',
    type=int, default=0,
    help="Number of Responses, values 0 - 1024. [default: '0']")

group.add_argument(
    '--alarm-rio-inputs',
    type=int, default=0,
    help="Number of SCS/RIO Inputs, values from 0 - 120. [default: '0']")

group.add_argument(
    '--alarm-rio-outputs',
    type=int, default=0,
    help="Number of SCS/RIO Outputs, values from 0 - 120. [default: '0']")

group = parser.add_argument_group('Logging options')
group.add_argument(
    '--verbosity',
    dest='log_verbosity', default='INFO', choices=(
        'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'),
    help='Verbosity of logging to emit [default: %(default)s]')

option = parser.parse_args()

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=option.log_verbosity,
    datefmt='%Y-%m-%d %H:%M:%S'
)

TOKEN = os.getenv('SUPERVISOR_TOKEN')
ALPINE_VERSION = "N/A" if os.getenv('ALPINE_VERSION') == None else os.getenv('ALPINE_VERSION')

supervisor_url = 'http://supervisor'
addon_info_url = f'{supervisor_url}/addons/self/info'

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}

try:
    response = requests.get(addon_info_url, headers=headers, timeout=5)
except:
    logger.error("Failed to connect to Home Assistant Supervisor")
else:
    if response.status_code == 200:
        addon_info = response.json()
        ADDON_SLUG = addon_info['data']['slug']
        ADDON_VERSION = addon_info['data']['version']
    else:
        logger.error("Failed to get Addon Info: Error Code %s, %s", response.status_code, response.reason)

logger.info('Importing the add-on configuration options')

MQTT_USER=option.broker_username
MQTT_PASSWORD=option.broker_password
MQTT_PORT=option.broker_port
MQTT_PROTOCOL=option.broker_protocol
MQTT_ENCRYPTION=option.broker_encryption    
MQTT_CA_CERT=option.broker_ca               
MQTT_CLIENT_CERT=option.broker_client_cert  
MQTT_CLIENT_KEY=option.broker_client_key    

def is_ipv4_address(address):
    try:
        ipaddress.ip_address(address)
        return True
    except ValueError:
        return False

def resolve_to_ip(fqdn):
    try:
        return socket.gethostbyname(fqdn)
    except socket.gaierror:
        return None

def get_ip_address(input_value):
    if is_ipv4_address(input_value):
        return input_value
    else:
        return resolve_to_ip(input_value)

def validate_port(_port, min=1, max=65535):
    try:
        port = int(_port)
        if min <= int(port) <= max:
            return True
        else:
            logging.error(f"Invalid parameter: {port}")     #Integer
            return False
    except Exception as e:
        logging.error(f"Invalid parameter: {_port}")        #Original passed value
        return False    
    
# Check to see if it's a Hostname.domain or IPv4 address. Resolve Hostname to IP.
COMFORT_ADDRESS=get_ip_address(option.comfort_address)
MQTT_SERVER=get_ip_address(option.broker_address)

COMFORT_PORT=int(option.comfort_port) if validate_port(option.comfort_port) else 1002
COMFORT_LOGIN_ID=option.comfort_login_id
COMFORT_CCLX_FILE=option.comfort_cclx_file
MQTT_LOG_LEVEL=option.log_verbosity if option.log_verbosity in ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'] else 'INFO'
COMFORT_INPUTS=int(option.alarm_inputs) if validate_port(option.alarm_inputs,8,MAX_ZONES) else 8
COMFORT_OUTPUTS=int(option.alarm_outputs) if validate_port(option.alarm_outputs,0,MAX_OUTPUTS) else 0
COMFORT_RESPONSES=int(option.alarm_responses) if validate_port(option.alarm_responses,0,MAX_RESPONSES) else 0
COMFORT_TIME=str(option.comfort_time)
COMFORT_RIO_INPUTS=int(option.alarm_rio_inputs) if validate_port(option.alarm_rio_inputs,0,120) else 0
COMFORT_RIO_OUTPUTS=int(option.alarm_rio_outputs) if validate_port(option.alarm_rio_outputs,0,120) else 0
COMFORT_BATTERY_STATUS_ID=int(option.comfort_battery_update) if int(option.comfort_battery_update) in [0,1]+list(range(33,40)) else 1

ALARMINPUTTOPIC = DOMAIN+"/input%d"                     #input1,input2,... input128 for every input. Physical Inputs (Default 8), Max 128
if COMFORT_INPUTS < 8:
    COMFORT_INPUTS = 8
if COMFORT_INPUTS > MAX_ZONES:                          # 128 is max. setting for possible future expansion. 96 currently supported by Cytech.
    COMFORT_INPUTS = MAX_ZONES
ALARMVIRTUALINPUTRANGE = range(1,int(COMFORT_INPUTS)+1) 
ALARMINPUTCOMMANDTOPIC = DOMAIN+"/input%d/set"          #input1,input2,... input128 for inputs, settable if configured as Virtual.

ALARMRIOINPUTTOPIC = DOMAIN+"/input%d"                  #input129,input130,... input248 for every input. Physical SCS/RIO Inputs (Default 0), Max 120, starting at 129.  
if int(COMFORT_RIO_INPUTS) < 0:
    COMFORT_RIO_INPUTS = 0
if int(COMFORT_RIO_INPUTS) > 120:
    COMFORT_RIO_INPUTS = 120
ALARMRIOINPUTRANGE = range(129,129+int(COMFORT_RIO_INPUTS))
ALARMRIOINPUTCOMMANDTOPIC = DOMAIN+"/input%d/set"       #input129,input130,... input248 for SCS/RIO inputs. Cannot set as Virtual Input.

ALARMOUTPUTTOPIC = DOMAIN+"/output%d"                   #output1,output2,... for every output
if COMFORT_OUTPUTS < 0:
    COMFORT_OUTPUTS = 0
if COMFORT_OUTPUTS > MAX_OUTPUTS:
    COMFORT_OUTPUTS = MAX_OUTPUTS
ALARMNUMBEROFOUTPUTS = COMFORT_OUTPUTS                  
ALARMOUTPUTCOMMANDTOPIC = DOMAIN+"/output%d/set"        #output1/set,output2/set,... for every output

ALARMRIOOUTPUTTOPIC = DOMAIN+"/output%d"                #output129,output130,... for every SCS/RIO output
if int(COMFORT_RIO_OUTPUTS) < 0:
    COMFORT_RIO_OUTPUTS = 0
if int(COMFORT_RIO_OUTPUTS) > 120:
    COMFORT_RIO_OUTPUTS = 120
ALARMRIOOUTPUTRANGE = range(129,129+int(COMFORT_RIO_OUTPUTS))    #set this according to your system. Physical SCS/RIO Outputs (Default 0), Max 120
ALARMRIOOUTPUTCOMMANDTOPIC = DOMAIN+"/output%d/set"     #output129,output130,... output248 for SCS/RIO outputs.

if COMFORT_RESPONSES < 0:
    COMFORT_RESPONSES = 0
if COMFORT_RESPONSES > 1024:
    COMFORT_RESPONSES = 1024
ALARMNUMBEROFRESPONSES = COMFORT_RESPONSES              #set in configuration according to your system. Default 0, Max 1024
ALARMRESPONSECOMMANDTOPIC = DOMAIN+"/response%d/set"    #response1,response2,... for every response

ALARMNUMBEROFFLAGS = 254                                # Max Flags for system
ALARMFLAGTOPIC = DOMAIN+"/flag%d"                       #flag1,flag2,...flag254
ALARMFLAGCOMMANDTOPIC = DOMAIN+"/flag%d/set"            #flag1/set,flag2/set,... flag254/set

ALARMNUMBEROFSENSORS = 32                               # Use system default = 32 (0-31)
ALARMSENSORTOPIC = DOMAIN+"/sensor%d"                   #sensor0,sensor1,...sensor31
ALARMSENSORCOMMANDTOPIC = DOMAIN+"/sensor%d/set"        #sensor0,sensor1,...sensor31

ALARMNUMBEROFCOUNTERS = 255                             # Hardcoded to 255
ALARMCOUNTERINPUTRANGE = DOMAIN+"/counter%d"            # each counter represents a value EG. light level
ALARMCOUNTERCOMMANDTOPIC = DOMAIN+"/counter%d/set"      # set the counter to a value for between 0 (off) to 255 (full on) or any signed 16-bit value.

logger.info('Completed importing addon configuration options')

# The following variables values were passed through via the Home Assistant add on configuration options
logger.debug('The following variable values were passed through via Home Assistant')
logger.debug('MQTT_USER = %s', MQTT_USER)
logger.debug('MQTT_PASSWORD = ******')
logger.debug('MQTT_SERVER = %s', MQTT_SERVER)

if not MQTT_ENCRYPTION: logger.debug('MQTT_PROTOCOL = %s/%s (Unsecure)', MQTT_PROTOCOL, MQTT_PORT)
else: logger.debug('MQTT_PROTOCOL = %s/%s (Encrypted)', MQTT_PROTOCOL, MQTT_PORT)

logger.debug('COMFORT_ADDRESS = %s', COMFORT_ADDRESS)
logger.debug('COMFORT_PORT = %s', COMFORT_PORT)
logger.debug('COMFORT_LOGIN_ID = ******')
logger.debug('COMFORT_CCLX_FILE = %s', COMFORT_CCLX_FILE)
logger.debug('COMFORT_BATTERY_STATUS_ID = %s', str(COMFORT_BATTERY_STATUS_ID))
logger.debug('MQTT_CA_CERT = %s', MQTT_CA_CERT)          
logger.debug('MQTT_CLIENT_CERT = %s', MQTT_CLIENT_CERT)  
logger.debug('MQTT_CLIENT_KEY = %s', MQTT_CLIENT_KEY)    

logger.debug('MQTT_LOG_LEVEL = %s', MQTT_LOG_LEVEL)
logger.debug('COMFORT_TIME= %s', COMFORT_TIME)

# Map HA variables to internal variables.

MQTTBROKERIP = MQTT_SERVER
MQTTBROKERPORT = int(MQTT_PORT)
MQTTUSERNAME = MQTT_USER
MQTTPASSWORD = MQTT_PASSWORD
COMFORTIP = COMFORT_ADDRESS
COMFORTPORT = int(COMFORT_PORT)
PINCODE = COMFORT_LOGIN_ID

BUFFER_SIZE = 4096
TIMEOUT = timedelta(seconds=30)                         #Comfort will disconnect if idle for 120 secs, so make sure this is less than that
RETRY = timedelta(seconds=10)

class ComfortLUUserLoggedIn(object):
    def __init__(self, datastr="", user=1):             
        if datastr:
            self.user = int(datastr[2:4], 16)
        else:
            self.user = int(user)

class ComfortIPInputActivationReport(object):
    def __init__(self, datastr="", input=0, state=0):
        if datastr:
            self.input = int(datastr[2:4], 16)
            self.state = int(datastr[4:6], 16)
        else:
            self.input = int(input)
            self.state = int(state)

class ComfortCTCounterActivationReport(object): # in format CT1EFF00 ie CT (counter) 1E = 30; state FF00 = 65280
    def __init__(self, datastr="", counter=0, value=0, state=0):
        if datastr:
            self.counter = int(datastr[2:4], 16)    #Integer value 3
            self.value = self.ComfortSigned16(int("%s%s" % (datastr[6:8], datastr[4:6]),16))            # Use new 16-bit format
            self.state = self.state = 1 if (int(datastr[4:6],16) > 0) else 0                            # 8-bit value used for state
        else:
            self.counter = counter
            self.value = value
            self.state = state

    def ComfortSigned16(self,value):                                            # Returns signed 16-bit value where required.
        return -(value & 0x8000) | (value & 0x7fff)
    
    ### Byte-Swap code below ###
    def HexToSigned16Decimal(self,value):                                       # Returns Signed Decimal value from HEX string EG. FFFF = -1
        return -(int(value,16) & 0x8000) | (int(value,16) & 0x7fff)

    def byte_swap_16_bit(self, hex_string):
        # Ensure the string is prefixed with '0x' for hex conversion            # Trying to cleanup strings.
        if not hex_string.startswith('0x'):
            hex_string = '0x' + hex_string
    
        # Convert hex string to integer
        value = int(hex_string, 16)
    
        # Perform byte swapping
        swapped_value = ((value << 8) & 0xFF00) | ((value >> 8) & 0x00FF)
    
        # Convert back to hex string, remove the leading '0x' and return 16-bit number.
        return hex(swapped_value)

class ComfortOPOutputActivationReport(object):
    def __init__(self, datastr="", output=0, state=0):
        if datastr:
            self.output = int(datastr[2:4], 16)
            self.state = int(datastr[4:6], 16)
        else:
            self.output = int(output)
            self.state = int(state)

class ComfortFLFlagActivationReport(object):
    def __init__(self, datastr="", flag=1, state=0):
        if datastr:
            self.flag = int(datastr[2:4], 16)
            self.state = int(datastr[4:6], 16)
        else:
            self.flag = int(flag)
            self.state = int(state)

class ComfortBYBypassActivationReport(object):

    global BYPASSEDZONES
    global COMFORT_INPUTS

    def __init__(self, datastr="", zone="0", state="0"):
        if datastr:
            self.zone = int(datastr[2:4],16)
            self.state = int(datastr[4:6],16)
        else:
            self.zone = int(zone,16)
            self.state = int(state,16)

        if (self.state == 0) and (self.zone <= int(COMFORT_INPUTS)):
            if (self.zone in BYPASSEDZONES):
                BYPASSEDZONES.remove(self.zone)
                if BYPASSEDZONES.count(-1) == 0 and len(BYPASSEDZONES) == 0:
                    BYPASSEDZONES.append(0)        
            else:
                logger.debug("ValueError Exception: Bypassed Zone (%s) does not appear in BYPASSEDZONES List[]", self.zone)
        elif (self.state == 1) and (self.zone <= int(COMFORT_INPUTS)):                     # State == 1 meaning must be in bypasszones
            if (self.zone not in BYPASSEDZONES):
                BYPASSEDZONES.append(self.zone)
            if BYPASSEDZONES.count(0) >= 1:        
                BYPASSEDZONES.remove(0)

        BYPASSEDZONES.sort(reverse=False)
        result_string = ','.join(map(str, BYPASSEDZONES))
        self.value = result_string

class ComfortZ_ReportAllZones(object):
    def __init__(self, data={}):

        global ZoneCache

        self.inputs = []
        b = (len(data) - 2) // 2            #variable number of zones reported
        self.max_zones = b * 8
        for i in range(1,b+1):
            inputbits = int(data[2*i:2*i+2],16)
            for j in range(0,8):
                self.inputs.append(ComfortIPInputActivationReport("", 8*(i-1)+1+j,(inputbits>>j) & 1))
                ZoneCache[8*(i-1)+1+j] = (inputbits>>j) & 1

class Comfort_Z_ReportAllZones(object):     #SCS/RIO z?
    def __init__(self, data={}):

        self.inputs = []    
        b = (len(data) - 2) // 2            #variable number of zones reported
        self.max_zones = b * 8
        for i in range(1,b+1):  
            inputbits = int(data[2*i:2*i+2],16)
            for j in range(0,8): 
                self.inputs.append(ComfortIPInputActivationReport("", 128+8*(i-1)+1+j,(inputbits>>j) & 1))


class Comfort_RSensorActivationReport(object):
    def __init__(self, datastr="", sensor=0, state=0):
        if datastr:
            self.sensor = int(datastr[2:4], 16)
            self.value = self.ComfortSigned16(int("%s%s" % (datastr[6:8], datastr[4:6]),16))    # Use new 16-bit format
        else:
            self.sensor = sensor
            self.value = state

    def ComfortSigned16(self,value):        # Returns signed 16-bit value where required.
        return -(value & 0x8000) | (value & 0x7fff)

class Comfort_R_ReportAllSensors(object):
    def __init__(self, data={}, sensor=0, value=0, counter=0, state=0):
        self.sensors = []
        self.counters = []
        b = (len(data) - 8) // 4             #Fixed number of sensors reported from r?01 command. 0-15 and 16-31.
        self.RegisterStart = int(data[4:6],16)
        self.RegisterType = int(data[2:4],16)
        for i in range(0,b):
            if self.RegisterType == 1:  #Sensor
                sensorbits = data[8+(4*i):8+(4*i)+4]
                #Swap bits here.
                #Change to Signed value here.
                self.value = int((sensorbits[2:4] + sensorbits[0:2]),16)
                self.sensor =  self.RegisterStart+i
                self.sensors.append(Comfort_RSensorActivationReport("", self.RegisterStart+i, self.value))
            else:
                counterbits = data[8+(4*i):8+(4*i)+4]   #0000
                self.value = int((counterbits[2:4] + counterbits[0:2]),16)
                self.state = 1 if (int(counterbits[0:2],16) > 0) else 0
                self.counter = self.RegisterStart+i
                self.counters.append(ComfortCTCounterActivationReport("", self.RegisterStart+i, self.value, self.state))
    
    def ComfortSigned16(self,value):     # Returns signed 16-bit value from HEX value.
        return -(value & 0x8000) | (value & 0x7fff)


class ComfortY_ReportAllOutputs(object):
    def __init__(self, data={}):
        self.outputs = []
        b = (len(data) - 2) // 2   #variable number of outputs reported
        self.max_zones = b * 8
        for i in range(1,b+1):
            outputbits = int(data[2*i:2*i+2],16)
            for j in range(0,8):
                self.outputs.append(ComfortOPOutputActivationReport("", 8*(i-1)+1+j,(outputbits>>j) & 1))

class Comfort_Y_ReportAllOutputs(object): 
    def __init__(self, data={}):    
        self.outputs = []           
        b = (len(data) - 2) // 2   #variable number of outputs reported
        self.max_zones = b * 8
        for i in range(1,b+1):  
            outputbits = int(data[2*i:2*i+2],16)
            for j in range(0,8):
                self.outputs.append(ComfortOPOutputActivationReport("", 128+8*(i-1)+1+j,(outputbits>>j) & 1))

class ComfortB_ReportAllBypassZones(object):

    def __init__(self, data={}):

        global BYPASSEDZONES    
        global CacheState
        global BypassCache          # Only for Comfort Zone Inputs, not for RIO Inputs.

        BYPASSEDZONES.clear()       #Clear contents and rebuild again.
        source_length = (len(data[4:]) * 4)    #96
        # Convert the string to a hexadecimal value
        source_hex = int(data[4:], 16)
        # Convert the hex number to binary string
        binary_number = bin(source_hex)[2:].zfill(source_length)  # Convert to binary and zero-fill to 24 bits indicating all zones
        # Determine the length of the binary number
        num_bits = len(binary_number)   #96
        # Extract 8-bit segments from the binary number
        eight_bit_segments = [binary_number[i:i+8] for i in range(0, num_bits, 8)]
        self.zones = []
        for i, segment in enumerate(eight_bit_segments, start=0):
            start_zone = 1 + (8 * i)
            for j in range(1, 9):   # Zone 1 to 8
                if (start_zone + j - 1) < 129:     # Max 128 zones
                    zone_number = int(start_zone + j - 1)
                    zone_state = int(segment[8 - j],2)
                    BypassCache[zone_number] = zone_state   # Populate Cache on startup.
                    if zone_state == 1 and zone_number <= int(COMFORT_INPUTS):       # Was 128, now configured Zones.
                        BYPASSEDZONES.append(zone_number)
                        self.zones.append(ComfortBYBypassActivationReport("", hex(zone_number), hex(zone_state)))
        CacheState = True

        if len(BYPASSEDZONES) == 0:
            BYPASSEDZONES.append(0)

        result_string = ','.join(map(str, BYPASSEDZONES))
        self.value = result_string

class Comfortf_ReportAllFlags(object):
    def __init__(self, data={}):
        self.flags = []         
        source_length = (len(data) * 4 - 16)

        # Convert the string to a hexadecimal value
        source_hex = int(data[4:], 16)
        # Convert the hex number to binary string
        binary_number = bin(source_hex)[2:].zfill(source_length)  # Convert to binary and zero-fill to 24 bits
        # Determine the length of the binary number
        num_bits = len(binary_number)
        # Extract 8-bit segments from the binary number
        eight_bit_segments = [binary_number[i:i+8] for i in range(0, num_bits, 8)]
        for i, segment in enumerate(eight_bit_segments, start=0):
            # Adjust flag numbering for subsequent iterations
            start_flag = 1 + (8 * i)
            # Extract individual bit values and assign to flags
            flags = {}
            for j in range(1, 9):   # Flag 1 to 8 (Saved as 0 - 7)
                if (start_flag + j - 1) < 255:
                    flag_name = "flag" + str(start_flag + j - 1)
                    flags[flag_name] = int(segment[8 - j],2)
                    self.flags.append(ComfortFLFlagActivationReport("", int(start_flag + j - 1),int(segment[8 - j],2) & 1))
            

#mode = { 00=Off, 01=Away, 02=Night, 03=Day, 04=Vacation }
class ComfortM_SecurityModeReport(object):
    def __init__(self, data={}):
        self.mode = int(data[2:4],16)
        if self.mode == 0: self.modename = "disarmed"; logger.info("Security Off")
        elif self.mode == 1: self.modename = "armed_away"; logger.info("Armed Away Mode")
        elif self.mode == 2: self.modename = "armed_night"; logger.info("Armed Night Mode")
        elif self.mode == 3: self.modename = "armed_home"; logger.info("Armed Day Mode")
        elif self.mode == 4: self.modename = "armed_vacation"; logger.info("Armed Vacation Mode")
        else: self.modename = "Unknown"; logger.info("Unknown Mode")

#nn 00 = Idle, 1 = Trouble, 2 = Alert, 3 = Alarm
class ComfortS_SecurityModeReport(object):
    def __init__(self, data={}):
        self.mode = int(data[2:4],16)
        if self.mode == 0: self.modename = "Idle"
        elif self.mode == 1: self.modename = "Trouble"
        elif self.mode == 2: self.modename = "Alert"
        elif self.mode == 3: self.modename = "Alarm"
        else: self.modename = "Unknown"     # Should never happen.

#zone = 00 means system can be armed, no open zones
class ComfortERArmReadyNotReady(object):
    def __init__(self, data={}):
        self.zone = int(data[2:4],16)

class ComfortAMSystemAlarmReport(object):
    def __init__(self, data={}):
        
        global ZONEMAPFILE
        global input_properties
        global ACFail

        self.alarm = int(data[2:4],16)
        self.triggered = True               # For Comfort Alarm State Alert, Trouble, Alarm
        self.parameter = int(data[4:6],16)
        low_battery = ['','Slave 1','Slave 2','Slave 3','Slave 4','Slave 5','Slave 6','Slave 7']
        if ZONEMAPFILE:
            if self.alarm == 0: self.message = "Intruder, Zone "+str(self.parameter)+" ("+ str(input_properties[str(self.parameter)]['Name'])+")"
            elif self.alarm == 1: self.message = str(input_properties[str(self.parameter)]['Name'])+" Trouble"
            elif self.alarm == 2: self.message = "Low Battery - "+('Main' if self.parameter == 1 else low_battery[(self.parameter - 32)])
            elif self.alarm == 3: 
                self.message = "Power Failure - "+('Main' if self.parameter == 1 else low_battery[(self.parameter - 32)])
                ACFail = True
            elif self.alarm == 4: self.message = "Phone Trouble"
            elif self.alarm == 5: self.message = "Duress"
            elif self.alarm == 6: self.message = "Arm Failure"
            elif self.alarm == 7: self.message = "Family Care"
            elif self.alarm == 8: self.message = "Security Off, User "+str(self.parameter); self.triggered = False
            elif self.alarm == 9: self.message = "System Armed, User "+str(self.parameter); self.triggered = False
            elif self.alarm == 10: self.message = "Tamper "+str(self.parameter)
            elif self.alarm == 12: self.message = "Entry Warning, Zone "+str(self.parameter)+" ("+str(input_properties[str(self.parameter)]['Name'])+")"; self.triggered = False
            elif self.alarm == 13: self.message = "Alarm Abort"; self.triggered = False
            elif self.alarm == 14: self.message = "Siren Tamper"
            elif self.alarm == 15: self.message = "Bypass, Zone "+str(self.parameter)+" ("+str(input_properties[str(self.parameter)]['Name'])+")"; self.triggered = False
            elif self.alarm == 17: self.message = "Dial Test, User "+str(self.parameter); self.triggered = False
            elif self.alarm == 19: self.message = "Entry Alert, Zone "+str(self.parameter)+" ("+str(input_properties[str(self.parameter)]['Name'])+")"; self.triggered = False
            elif self.alarm == 20: self.message = "Fire"
            elif self.alarm == 21: self.message = "Panic"
            elif self.alarm == 22: self.message = "GSM Trouble "+str(self.parameter)
            elif self.alarm == 23: self.message = "New Message, User "+str(self.parameter); self.triggered = False
            elif self.alarm == 24: self.message = "Doorbell "+str(self.parameter); self.triggered = False
            elif self.alarm == 25: self.message = "Comms Failure RS485 id "+str(self.parameter)
            elif self.alarm == 26: self.message = "Signin Tamper "+str(self.parameter)
            else: self.message = "Unknown("+str(self.alarm)+")"
        else:
            if self.alarm == 0: self.message = "Intruder, Zone "+str(self.parameter)
            elif self.alarm == 1: self.message = "Zone "+str(self.parameter)+" Trouble"
            elif self.alarm == 2: self.message = "Low Battery - "+('Main' if self.parameter == 1 else low_battery[(self.parameter - 32)])
            elif self.alarm == 3: 
                self.message = "Power Failure - "+('Main' if self.parameter == 1 else low_battery[(self.parameter - 32)])
                ACFail = True
            elif self.alarm == 4: self.message = "Phone Trouble"
            elif self.alarm == 5: self.message = "Duress"
            elif self.alarm == 6: self.message = "Arm Failure"
            elif self.alarm == 7: self.message = "Family Care"
            elif self.alarm == 8: self.message = "Security Off, User "+str(self.parameter); self.triggered = False
            elif self.alarm == 9: self.message = "System Armed, User "+str(self.parameter); self.triggered = False
            elif self.alarm == 10: self.message = "Tamper "+str(self.parameter)
            elif self.alarm == 12: self.message = "Entry Warning, Zone "+str(self.parameter); self.triggered = False
            elif self.alarm == 13: self.message = "Alarm Abort"; self.triggered = False
            elif self.alarm == 14: self.message = "Siren Tamper"
            elif self.alarm == 15: self.message = "Bypass, Zone "+str(self.parameter); self.triggered = False
            elif self.alarm == 17: self.message = "Dial Test, User "+str(self.parameter); self.triggered = False
            elif self.alarm == 19: self.message = "Entry Alert, Zone "+str(self.parameter); self.triggered = False
            elif self.alarm == 20: self.message = "Fire"
            elif self.alarm == 21: self.message = "Panic"
            elif self.alarm == 22: self.message = "GSM Trouble "+str(self.parameter)
            elif self.alarm == 23: self.message = "New Message, User "+str(self.parameter); self.triggered = False
            elif self.alarm == 24: self.message = "Doorbell "+str(self.parameter); self.triggered = False
            elif self.alarm == 25: self.message = "Comms Failure RS485 id "+str(self.parameter)
            elif self.alarm == 26: self.message = "Signin Tamper "+str(self.parameter)
            else: self.message = "Unknown("+str(self.alarm)+")"

class ComfortALSystemAlarmReport(object):
    def __init__(self, data={}):
        
        global ZONEMAPFILE
        global input_properties
        global ALARMSTATE           # Numerical value for state. 0=Idle, 1=Trouble, 2=Alert, 3=Alarm

        self.priority = ALARMSTATE
        self.alarm = int(data[2:4],16)
        self.triggered = True               # For Comfort Alarm State Alert, Trouble, Alarm
        self.state = int(data[6:8],16)
        low_battery = ['','Slave 1','Slave 2','Slave 3','Slave 4','Slave 5','Slave 6','Slave 7']
        alarm_types = ['No Alarm','Intruder Alarm','Duress','Phone Line Trouble','Arm Fail','Zone Trouble','Zone Alert','Low Battery',
                       'Power Fail','Panic','Entry Alert','Tamper','Fire','Gas','Family Care','Perimeter Alert','Bypass Zone','System Disarmed',
                       'CMS Test','System Armed','Alarm Abort','Entry Warning','Siren Trouble','Unused','RS485 Comms Fail','Doorbell','Homesafe',
                       'Dial Test','SMS Trouble','New Message','Engineer Sign in','Sign-in Tamper']
        if self.state > self.priority:
            self.priority = self.state
            ALARMSTATE = self.state  # Save new state
        elif self.state == 0:
            ALARMSTATE = 0


class Comfort_A_SecurityInformationReport(object):      #  For future development !!!
    #a?000000000000000000
    def __init__(self, data={}):
            
        global ACFail

        self.AA = int(data[2:4],16)     #AA is the current Alarm Type 01 to 1FH (Defaults can be changed in Comfigurator)
        self.SS = int(data[4:6],16)     #SS is alarm state 0-3 (Idle, Trouble, Alert, Alarm)
        self.XX = int(data[6:8],16)     #XX is Trouble bits
        self.YY = int(data[8:10],16)    #YY is for Spare Trouble Bits, 0 if unused
        self.BB = int(data[10:12],16)   #BB = Low Battery ID = 1 for Comfort or none
        self.zz = int(data[12:14],16)   #zz = Zone Trouble number, =0 if none
        self.RR = int(data[14:16],16)   #RR = RS485 Trouble ID, = 0 if none
        self.TT = int(data[16:18],16)   #TT = Tamper ID = 0 if none
        self.GG = int(data[18:20],16)   #GG = GSM ID =0 if no trouble
        alarm_type = ['','Intruder','Duress','LineCut','ArmFail','ZoneTrouble','ZoneAlert','LowBattery', 'PowerFail', 'Panic', 'EntryAlert', \
                      'Tamper','Fire','Gas','FamilyCare','Perimeter', 'BypassZone','Disarm','CMSTest','SystemArmed', 'AlarmAbort', 'EntryWarning', \
                      'SirenTrouble','AlarmType23', 'RS485Comms','Doorbell','HomeSafe','DialTest','AlarmType28','NewMessage','Temperature','SigninTamper']
        alarm_state = ['Idle','Trouble','Alert','Alarm']
        low_battery = ['', 'Main','Slave 1','Slave 2','Slave 3','Slave 4','Slave 5','Slave 6','Slave 7']
        troublebits = ['AC Failure','Low Battery','Zone Trouble','RS485 Comms Fail','Tamper','Phone Trouble','GSM Trouble','Unknown']
        self.type = alarm_type[self.AA]
        self.state = alarm_state[self.SS]
        #self.battery = None
        self.acfail = (int(data[6:8],16) >> 0) & 1   #XX = AC Fail, bit 0. 0=AC OK, 1=AC Fail
        if self.acfail == 1: 
            ACFail = True
        elif self.acfail == 0: 
            ACFail = False
        if self.type == "LowBattery" and self.BB <= 1: self.battery = low_battery[1]
        #elif self.type == "LowBattery" and self.BB - 31 in low_battery:self.battery = low_battery[(self.BB - 31)]
        elif self.type == "LowBattery" and 0 <= (self.BB - 31) < len(low_battery):self.battery = low_battery[self.BB - 31]
        else:self.battery = "Unknown"

class ComfortARSystemAlarmReport(object):
    def __init__(self, data={}):
        global ZONEMAPFILE
        global input_properties
        global ACFail

        self.alarm = int(data[2:4],16)
        self.triggered = True   #for comfort alarm state Alert, Trouble, Alarm
        self.parameter = int(data[4:6],16)
        low_battery = ['','Slave 1','Slave 2','Slave 3','Slave 4','Slave 5','Slave 6','Slave 7']
        if ZONEMAPFILE:
            if self.alarm == 1: self.message = str(input_properties[str(self.parameter)]['Name'])+" Trouble Restore"
            elif self.alarm == 2: self.message = "Low Battery - "+('Main' if self.parameter == 1 else low_battery[(self.parameter - 32)])+" Restore"
            elif self.alarm == 3: 
                self.message = "Power Failure - "+('Main' if self.parameter == 1 else low_battery[(self.parameter - 32)])+" Restore"
                ACFail = False
            elif self.alarm == 4: self.message = "Phone Trouble"+" Restore"
            elif self.alarm == 10: self.message = "Tamper "+str(self.parameter)+" Restore"
            elif self.alarm == 14: self.message = "Siren Tamper"+" Restore"
            elif self.alarm == 22: self.message = "GSM Trouble "+str(self.parameter)+" Restore"
            elif self.alarm == 25: self.message = "Comms Failure RS485 id"+str(self.parameter)+" Restore"
            else: self.message = "Unknown("+str(self.alarm)+")"
        else:
            if self.alarm == 1: self.message = "Zone "+str(self.parameter)+" Trouble"+" Restore"
            elif self.alarm == 2: self.message = "Low Battery - "+('Main' if self.parameter == 1 else low_battery[(self.parameter - 32)])+" Restore"
            elif self.alarm == 3: 
                self.message = "Power Failure - "+('Main' if self.parameter == 1 else low_battery[(self.parameter - 32)])+" Restore"
                ACFail = False
            elif self.alarm == 4: self.message = "Phone Trouble"+" Restore"
            elif self.alarm == 10: self.message = "Tamper "+str(self.parameter)+" Restore"
            elif self.alarm == 14: self.message = "Siren Tamper"+" Restore"
            elif self.alarm == 22: self.message = "GSM Trouble "+str(self.parameter)+" Restore"
            elif self.alarm == 25: self.message = "Comms Failure RS485 id"+str(self.parameter)+" Restore"
            else: self.message = "Unknown("+str(self.alarm)+")"


class ComfortV_SystemTypeReport(object):
    def __init__(self, data={}):
        self.filesystem = int(data[8:10],16)    # 34 for Ultra II
        self.version = int(data[4:6],16)        # 7.
        self.revision = int(data[6:8],16)       # .210
        self.firmware = int(data[2:4],16)       # 254

class Comfort_U_SystemCPUTypeReport(object):

    #global device_properties
    
    def __init__(self, data={}):
       
        self.cputype = "N/A"

        if len(data) < 14:
            self.cputype = "N/A"
        else:
            identifier = int(data[12:14],16)
            if identifier == 1:
                self.cputype = "ARM"
            elif identifier == 0:
                self.cputype = "Toshiba"


class Comfort_EL_HardwareModelReport(object):
    def __init__(self, data={}):

        global device_properties

        self.hardwaremodel = "N/A"
        if len(data) < 14:
            self.hardwaremodel = "N/A"
        else:
            for i in range(4,len(data),2):
                if data[i:i+2] == 'FF':
                    device_properties['sem_id'] = int(i/2-2)
                    logging.debug("%s Installed SEM(s) detected", str(device_properties['sem_id']))
                    break
            identifier = int(data[3:4],16)
            if identifier == 1:
                if int(device_properties['ComfortFileSystem']) == 34:
                    self.hardwaremodel = "CM9000-ULT"
                elif int(device_properties['ComfortFileSystem']) == 31:
                    self.hardwaremodel = "CM9000-OPT"
                else:
                    self.hardwaremodel = models[int(device_properties['ComfortFileSystem'])]
            elif identifier == 0:
                if int(device_properties['ComfortFileSystem']) == 34:
                    self.hardwaremodel = "CM9001-ULT"
                elif int(device_properties['ComfortFileSystem']) == 31:
                    self.hardwaremodel = "CM9001-OPT"
                else:
                    self.hardwaremodel = models[int(device_properties['ComfortFileSystem'])]

class Comfort_D_SystemVoltageReport(object):
    def __init__(self, data={}):

        global device_properties
        global BatteryVoltageNameList
        global ChargerVoltageNameList
        global BatteryVoltageList
        global ChargerVoltageList
        global BatterySlaveIDs
        global ChargerSlaveIDs
        global ACFail

        if len(data) < 6:
            return
        query_type = int(data[4:6],16)
        id = int(data[2:4],16)

        for x in range(6, len(data), 2):
            value = int(data[x:x+2],16)

            if query_type == 2 and value > 10:      # Set to a value larger than 0V to indicate AC Ok.
                ACFail = False

            #voltage = str(format(round(((value/255)*15.5),2), ".2f")) if value < 255 else '-1'  # Old Formula used for Batteries.
            #voltage = str(format(round(((value/255)*(3.3/2.71)*15),2), ".2f")) if value < 255 else '-1'  # New Formula used for DC Supply voltage.
            if query_type == 1:
                #voltage = str(format(round(((value/255)*15.522),2), ".2f")) if value < 255 else '-1'  # Formula used for Batteries.
                if ACFail == False:
                    voltage =  str(format(round(((value/255)*(3.3/2.7)*12.7 - 0.75),2), ".2f")) if value < 255 else '-1'  # - testing.
                else:
                    voltage =  str(format(round(((value/255)*(3.3/2.7)*12.7 + 0.35),2), ".2f")) if value < 255 else '-1'  # - testing.

                #voltage = str(format(round(((value/255)*15.5),2), ".2f")) if value < 255 else '-1'  # Formula used for Batteries.
                if id == 0:
                    device_properties[BatteryVoltageNameList[(x-6)/2]] = voltage
                    BatteryVoltageList[(x-6)/2] = voltage
                elif (id == 1 or id > 32) and id <= 39:
                    device_properties[BatterySlaveIDs[id]] = voltage
                    id = (id - 32) if id > 1 else 0
                    BatteryVoltageList[id] = voltage
                else:
                    return
            elif query_type == 2:
                #voltage = str(format(round(((value/255)*(3.3/2.71)*15),2), ".2f")) if value < 255 else '-1'  # New Formula used for DC Supply voltage.
                voltage =  str(format(round(((value/255)*(3.3/2.7)*14.9),2), ".2f")) if value < 255 else '-1'  # New Formula used for DC Supply voltage - testing.
                if id == 0:
                    device_properties[ChargerVoltageNameList[(x-6)/2]] = voltage
                    ChargerVoltageList[(x-6)/2] = voltage
                elif (id == 1 or id > 32) and id <= 39:
                    device_properties[ChargerSlaveIDs[id]] = voltage
                    id = (id - 32) if id > 1 else 0
                    ChargerVoltageList[id] = voltage
                else:
                    return

        if query_type == 1:
            self.BatteryStatus = self.Battery_Status(BatteryVoltageList.values())
            device_properties['BatteryStatus'] = self.BatteryStatus
        elif query_type == 2:
            self.ChargerStatus = self.Charger_Status(ChargerVoltageList.values())
            device_properties['ChargerStatus'] = self.ChargerStatus

    def Battery_Status(self, voltages):  # Tuple of all voltages.
        state = ["Ok","Warning","Critical"]
        index = []
        for voltage in voltages:
            if float(voltage) == -1:
                index.append(0)
            elif float(voltage) > 15:           # Critical Overcharge
                index.append(2)
            elif float(voltage) > 14.6:         # Overcharge
                index.append(1)
            elif float(voltage) <= 9.5:         # Discharged/Critical Low Charge or No Charge
                index.append(2)
            elif float(voltage) < 11.5:         # Severely Discharged/Low Charge
                index.append(1)
            else:
                index.append(0)
        return state[max(index)]

    def Charger_Status(self, voltages):  # Tuple of all voltages.
        state = ["Ok","Warning","Critical"]
        index = []
        for voltage in voltages:
            if float(voltage) == -1:
                index.append(0)
            elif float(voltage) > 18:           # Critical High Voltage
                index.append(2)
            elif float(voltage) > 17:           # High Voltage
                index.append(1)
            elif float(voltage) <= 7:           # Critical Low or No Voltage output
                index.append(2)
            elif float(voltage) < 12:           # Low Voltage
                index.append(1)
            else:
                index.append(0)
        return state[max(index)]
    
class ComfortSN_SerialNumberReport(object):     # Possible Comfort SN decode issue. Sometimes Comfort reports 'Illegal' serial number.
    def __init__(self, data={}):

        if len(data) < 12:
            self.serial_number = "Invalid"
            self.refreshkey = "00000000"
            return
        else:
            # Decoding if Comfort implements SN reliably. Some systems are Invalid or Unsupported.
            DD = data[4:6]
            CC = data[6:8]
            BB = data[8:10]
            AA = data[10:12]
    
            dec_string = str(int(AA+BB+CC+DD,16)).zfill(8)
            dec_len = len(str(dec_string))
            prefix = int(dec_string[0:dec_len-6])
            if 0 < prefix <= 26:
                self.serial_number = str(chr(prefix + 64)) + dec_string[(dec_len-6):dec_len]
            elif data[4:12] == 'FFFFFFFF':
                self.serial_number = "Unassigned"
            elif data[4:12] == '00000000':
                self.serial_number = "Not Supported"
            else:
                self.serial_number = "Invalid"

            self.refreshkey = data[4:12]

class ComfortEXEntryExitDelayStarted(object):
    def __init__(self, data={}):
        self.type = int(data[2:4],16)
        self.delay = int(data[4:6],16)

class Comfort2(mqtt.Client):

    global FIRST_LOGIN
    global RUN

    def init(self, mqtt_ip, mqtt_port, mqtt_username, mqtt_password, comfort_ip, comfort_port, comfort_pincode, mqtt_version):
        self.mqtt_ip = mqtt_ip
        self.mqtt_port = mqtt_port
        self.comfort_ip = comfort_ip
        self.comfort_port = comfort_port
        self.comfort_pincode = comfort_pincode
        self.connected = False
        self.username_pw_set(mqtt_username, mqtt_password)
        self.version = mqtt_version

    def handler(self, signum, frame):                 # Ctrl-Z Keyboard Interrupt
        logger.debug('SIGTSTP (Ctrl-Z) intercepted')

    def sigquit_handler(self, signum, frame):         # Ctrl-\ Keyboard Interrupt
        global RUN
        logger.debug("SIGQUIT intercepted")
        RUN = False

    if os.name != 'nt':
        signal.signal(signal.SIGTSTP, handler)

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc, properties):

        global RUN
        global BROKERCONNECTED
        global FIRST_LOGIN
        global device_properties

        FIRST_LOGIN = True      # Set to True to start refresh on_connect
        
        if rc == 'Success':

            BROKERCONNECTED = True
            device_properties['BridgeConnected'] = 1

            logger.info('MQTT Broker Connection %s', str(rc))

            time.sleep(0.25)    # Short wait for MQTT to be ready to accept commands.

            # You need to subscribe to your own topics to enable publish messages activating Comfort entities.
            self.subscribe(ALARMCOMMANDTOPIC)
            self.subscribe(REFRESHTOPIC)
            self.subscribe(BATTERYREFRESHTOPIC)
            self.subscribe(DOMAIN)
            self.subscribe("homeassistant/status")      # Track Status changes for Home Assistant via MQTT Broker.

            for i in range(1, ALARMNUMBEROFOUTPUTS + 1):
                self.subscribe(ALARMOUTPUTCOMMANDTOPIC % i)
            
            if ALARMNUMBEROFOUTPUTS > 0:
                logger.debug("Subscribed to %d Zone Outputs", ALARMNUMBEROFOUTPUTS)
            else:
                logger.debug("Not Subscribed to any Zone Outputs")

            for i in ALARMVIRTUALINPUTRANGE: #for virtual inputs #inputs+1 to 128
                self.subscribe(ALARMINPUTCOMMANDTOPIC % i)

            logger.debug("Subscribed to %d Zone Inputs", ALARMVIRTUALINPUTRANGE[-1])

            for i in ALARMRIOINPUTRANGE: #for inputs 129 to Max Value
                self.subscribe(ALARMRIOINPUTCOMMANDTOPIC % i)

            if COMFORT_RIO_INPUTS > 0:              
                logger.debug("Subscribed to %d RIO Inputs", ALARMRIOINPUTRANGE[-1] - 128)
            else:
                logger.debug("Not Subscribed to any RIO Inputs")

            for i in ALARMRIOOUTPUTRANGE: #for outputs 129 to Max Value
                self.subscribe(ALARMRIOOUTPUTCOMMANDTOPIC % i)

            if COMFORT_RIO_OUTPUTS > 0:              
                logger.debug("Subscribed to %d RIO Outputs", ALARMRIOOUTPUTRANGE[-1] - 128)
            else:
                logger.debug("Not Subscribed to any RIO Outputs")

            for i in range(1, ALARMNUMBEROFFLAGS + 1):
                if i >= 255:
                    break
                self.subscribe(ALARMFLAGCOMMANDTOPIC % i)
            logger.debug("Subscribed to %d Flags", ALARMNUMBEROFFLAGS)
                
                ## Sensors ##
            for i in range(0, ALARMNUMBEROFSENSORS):
                self.subscribe(ALARMSENSORCOMMANDTOPIC % i)
            logger.debug("Subscribed to %d Sensors", ALARMNUMBEROFSENSORS)

            for i in range(0, ALARMNUMBEROFCOUNTERS + 1):
                self.subscribe(ALARMCOUNTERCOMMANDTOPIC % i)    # Value or Level
            logger.debug("Subscribed to %d Counters", ALARMNUMBEROFCOUNTERS)

            for i in range(1, ALARMNUMBEROFRESPONSES + 1):      # Responses as specified from HA options.
                self.subscribe(ALARMRESPONSECOMMANDTOPIC % i)
            if ALARMNUMBEROFRESPONSES > 0:
                logger.debug("Subscribed to %d Responses", ALARMNUMBEROFRESPONSES)
            else:
                logger.debug("Not Subscribed to any Responses")

            if FIRST_LOGIN == True:
                logger.debug("Synchronizing Comfort Data...")
                self.readcurrentstate()
                logger.debug("Synchronization Done.")
            
        else:
            logger.error('MQTT Broker Connection Failed (%s)', str(rc))
            BROKERCONNECTED = False
            device_properties['BridgeConnected'] = 0

    def on_disconnect(self, client, userdata, flags, reasonCode, properties):  #client, userdata, flags, reason_code, properties

        global FIRST_LOGIN
        global BROKERCONNECTED
        global device_properties

        if reasonCode == 0:
            logger.info('MQTT Broker Disconnect Successfull (%s)', str(reasonCode))
        else:
            BROKERCONNECTED = False
            device_properties['BridgeConnected'] = 0
            logger.error('MQTT Broker Connection Failed (%s). Check Network or MQTT Broker connection settings', str(reasonCode))
            FIRST_LOGIN = True

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):    #=0

        global SAVEDTIME
        global COMFORT_KEY

        msgstr = msg.payload.decode()
        if msg.topic == ALARMCOMMANDTOPIC:      
            if self.connected:
                if msgstr == "ARM_VACATION":
                    self.comfortsock.sendall(("\x03m!04"+self.comfort_pincode+"\r").encode()) #Local arm to 04 vacation mode. Requires # for open zones
                    SAVEDTIME = datetime.now()
                    self.publish(ALARMSTATETOPIC, "arming",qos=2,retain=False)
                elif msgstr == "ARM_HOME":
                    self.comfortsock.sendall(("\x03m!03"+self.comfort_pincode+"\r").encode()) #Local arm to 03 day mode. Requires # for open zones
                    SAVEDTIME = datetime.now()
                    self.publish(ALARMSTATETOPIC, "arming",qos=2,retain=False)
                elif msgstr == "ARM_NIGHT":
                    self.comfortsock.sendall(("\x03m!02"+self.comfort_pincode+"\r").encode()) #Local arm to 02 night mode. Requires # for open zones
                    SAVEDTIME = datetime.now()
                    self.publish(ALARMSTATETOPIC, "arming",qos=2,retain=False)
                elif msgstr == "ARM_AWAY":
                    self.comfortsock.sendall(("\x03m!01"+self.comfort_pincode+"\r").encode()) #Local arm to 01 away mode. Requires # for open zones + Exit door
                    SAVEDTIME = datetime.now()
                    self.publish(ALARMSTATETOPIC, "arming",qos=2,retain=False)
                elif msgstr == "REM_ARM_AWAY":
                    self.comfortsock.sendall(("\x03M!01"+self.comfort_pincode+"\r").encode()) #Remote arm to 01 away mode. Requires # for open zones
                    SAVEDTIME = datetime.now()
                    self.publish(ALARMSTATETOPIC, "arming",qos=2,retain=False)
                elif msgstr == "ARM_CUSTOM_BYPASS":
                    self.comfortsock.sendall("\x03KD1A\r".encode())                           #Send '#' key code (KD1A)
                    SAVEDTIME = datetime.now()
                elif msgstr == "DISARM":
                    self.comfortsock.sendall(("\x03m!00"+self.comfort_pincode+"\r").encode()) #Local arm to 00. disarm mode.
                    SAVEDTIME = datetime.now()

        elif msg.topic.startswith(DOMAIN) and msg.topic.endswith("/refresh"):
            if msgstr == COMFORT_KEY:
                logger.info("Valid Refresh AUTH key detected, initiating MQTT refresh...")
                if COMFORT_CCLX_FILE != None:
                    config_filename = self.sanitize_filename(COMFORT_CCLX_FILE,'cclx')
                    if config_filename:
                        self.add_descriptions(Path("/config/" + config_filename))
                self.readcurrentstate()
        
        elif msg.topic.startswith(DOMAIN) and msg.topic.endswith("/battery_update"):

            Devices = ['0','1']        # Mainboard + Installed Slaves EG. ['0', '1','33','34','35' ti '39'].
            for device in range(0, int(device_properties['sem_id'])):
                Devices.append(str(device + 33))    # First Slave at address 33 DEC.

            msgstr_cleaned = msgstr.strip('"')
            if msgstr_cleaned in Devices and (str(device_properties['CPUType']) == 'ARM' or str(device_properties['CPUType']) == 'Toshiba'):
                
                ID = str(f"{int(msgstr_cleaned):02X}")

                #logger.info("msgstr: %s", msgstr.strip('"'))
                #logger.info("msgstr type: %s", type(msgstr.strip('"')))

                #logger.info("ID: %s", ID)
                if msgstr_cleaned == '0':
                    Command = "\x03D?0000\r"
                    self.comfortsock.sendall(Command.encode()) # Battery and DC Supply Status Update
                else:
                    Command = "\x03D?" + ID + "01\r"
                    self.comfortsock.sendall(Command.encode()) # Battery Status Update
                    time.sleep(0.1)
                    Command = "\x03D?" + ID + "02\r"
                    self.comfortsock.sendall(Command.encode()) # DC Supply Status Update
                    time.sleep(0.1)
                SAVEDTIME = datetime.now()
            else:
                logger.warning("Unsupported MQTT Battery Update query received for ID: %s.", msgstr_cleaned)
                logger.warning("Valid ID's: [0,1,33-39] with ARM-powered Comfort is required.")

        elif msg.topic.startswith("homeassistant") and msg.topic.endswith("/status"):
            if msgstr == "online":
                logger.info("Home Assistant Status: %s", msgstr)
                if COMFORT_CCLX_FILE != None:
                    config_filename = self.sanitize_filename(COMFORT_CCLX_FILE,'cclx')
                    if config_filename:
                        self.add_descriptions(Path("/config/" + config_filename))
                self.readcurrentstate()

            elif msgstr == "offline":
                logger.info("Home Assistant Status: %s", msgstr)

        elif msg.topic.startswith(DOMAIN+"/output") and msg.topic.endswith("/set"):
            output = int(msg.topic.split("/")[1][6:])
            try:
                state = int(msgstr)
            except ValueError:
                logger.debug("Invalid 'output%s/set' value '%s'. Only Integers allowed.", output, msgstr)
                return
            if self.connected:
                if state >= 0 and state < 5:
                    self.comfortsock.sendall(("\x03O!%02X%02X\r" % (output, state)).encode())
                    SAVEDTIME = datetime.now()
        elif msg.topic.startswith(DOMAIN+"/response") and msg.topic.endswith("/set"):
            response = int(msg.topic.split("/")[1][8:])
            if self.connected:
                if (response in range(1, ALARMNUMBEROFRESPONSES + 1)) and (response in range(256, 1025)):   # Check for  valid response numbers > 255 but less than Max.
                    result = self.DecimalToSigned16(response)                                               # Returns hex value.
                    self.comfortsock.sendall(("\x03R!%s\r" % result).encode())                              # Response with 16-bit converted hex number
                    SAVEDTIME = datetime.now()
                elif (response in range(1, ALARMNUMBEROFRESPONSES + 1)) and (response in range(1, 256)):    # Check for 8-bit values
                    self.comfortsock.sendall(("\x03R!%02X\r" % response).encode())                          # Response with 8-bit number
                    SAVEDTIME = datetime.now()
                logger.debug("Activating Response %d",response )
        elif msg.topic.startswith(DOMAIN+"/input") and msg.topic.endswith("/set"):                          # Can only set the State, the Bypass, Name and Time cannot be changed.
            virtualinput = int(msg.topic.split("/")[1][5:])
            try:
                state = int(msgstr)
            except ValueError:
                logger.debug("Invalid 'input%s/set' value '%s'. Only Integers allowed.", virtualinput, msgstr)
                return
            if self.connected:
                self.comfortsock.sendall(("\x03I!%02X%02X\r" % (virtualinput, state)).encode())
                SAVEDTIME = datetime.now()
        elif msg.topic.startswith(DOMAIN+"/flag") and msg.topic.endswith("/set"):
            flag = int(msg.topic.split("/")[1][4:])
            try:
                state = int(msgstr)
            except ValueError:
                logger.debug("Invalid 'flag%s/set' value '%s'. Only Integers allowed.", flag, msgstr)
                return
            if self.connected:
                self.comfortsock.sendall(("\x03F!%02X%02X\r" % (flag, state)).encode()) #was F!
                SAVEDTIME = datetime.now()
        elif msg.topic.startswith(DOMAIN+"/counter") and msg.topic.endswith("/set"): # counter set
            counter = int(msg.topic.split("/")[1][7:])
            if not msgstr.isnumeric() and not msgstr == "ON" and not msgstr == "OFF":
                logger.debug("Invalid Counter%s Set value detected ('%s'), only 'ON', 'OFF' and Integer values allowed", str(counter), str(msgstr))
            elif msgstr == "ON":
                state = 255
                if self.connected:
                    self.comfortsock.sendall(("\x03C!%02X%s\r" % (counter, self.DecimalToSigned16(state))).encode()) # counter needs 16 bit signed number
                    SAVEDTIME = datetime.now()
            elif msgstr == "OFF":
                state = 0
                if self.connected:
                    self.comfortsock.sendall(("\x03C!%02X%s\r" % (counter, self.DecimalToSigned16(state))).encode()) # counter needs 16 bit signed number
                    SAVEDTIME = datetime.now()
            else:
                state = int(msgstr)
                if self.connected:
                    self.comfortsock.sendall(("\x03C!%02X%s\r" % (counter, self.DecimalToSigned16(state))).encode()) # counter needs 16 bit signed number
                    SAVEDTIME = datetime.now()
        elif msg.topic.startswith(DOMAIN+"/sensor") and msg.topic.endswith("/set"): # sensor set
            sensor = int(msg.topic.split("/")[1][6:])
            try:
                state = int(msgstr)
            except ValueError:
                logger.debug("Invalid 'sensor%s/set' value '%s'. Only Integers allowed.", sensor, msgstr)
                return
            if self.connected:
                self.comfortsock.sendall(("\x03s!%02X%s\r" % (sensor, self.DecimalToSigned16(state))).encode()) # sensor needs 16 bit signed number
                SAVEDTIME = datetime.now()

    def DecimalToSigned16(self,value):      # Returns Comfort corrected HEX string value from signed 16-bit decimal value.
        return ('{:04X}'.format((int((value & 0xff) * 0x100 + (value & 0xff00) / 0x100))) )
    
    def CheckZoneNameFormat(self,value):      # Checks CSV file Zone Name to only contain valid characters. Return False if it fails else True
        pattern = r'^(?![ ]{1,}).{1}[a-zA-Z0-9_ -/]+$'
        return bool(re.match(pattern, value))
    
    def CheckIndexNumberFormat(self,value,max_index = 1024):      # Checks CSV file Zone Number to only contain valid characters. Return False if it fails else True
        pattern = r'^[0-9]+$'
        if bool(re.match(pattern, value)):
            if value.isnumeric() & (int(value) <= max_index):
                return True
            else:
                return False
        else:
            return False
    
    def HexToSigned16Decimal(self,value):        # Returns Signed Decimal value from HEX string EG. FFFF = -1
        return -(int(value,16) & 0x8000) | (int(value,16) & 0x7fff)

    def byte_swap_16_bit(self, hex_string):
        # Ensure the string is prefixed with '0x' for hex conversion
        if not hex_string.startswith('0x'):
            hex_string = '0x' + hex_string
    
        # Convert hex string to integer
        value = int(hex_string, 16)
        # Perform byte swapping
        swapped_value = ((value << 8) & 0xFF00) | ((value >> 8) & 0x00FF)
        # Convert back to hex string and return
        return hex(swapped_value)[2:].upper().zfill(4)

    def on_publish(self, client, obj, mid, reason_codes, properties):
        pass

    def on_subscribe(self, client, userdata, mid, reason_codes, properties):
        for sub_result in reason_codes:
            if sub_result == 1:
                pass
            if sub_result >= 128:
                logger.debug("Error processing subscribe message")

    def on_log(self, client, userdata, level, buf):
        pass

    def entryexit_timer(self):
        self.publish(ALARMTIMERTOPIC, self.entryexitdelay,qos=2,retain=True)
        self.entryexitdelay -= 1
        if self.entryexitdelay >= 0:
            threading.Timer(1, self.entryexit_timer).start()

    def _send_keepalive_and_check(self, max_attempts=3, delay_between_attempts=2):
        """
        Send a keepalive (cc00) command and verify the socket is still alive.
        Retry up to max_attempts times before declaring the socket dead.
        """
        #logger.debug("Starting keepalive health check (%d attempts allowed)", max_attempts)

        for attempt in range(1, max_attempts + 1):
            try:
                #logger.debug("Keepalive attempt %d of %d", attempt, max_attempts)
            
                # Send keepalive command
                self.SendCommand("cc00")
                time.sleep(0.1)

                # Temporarily shorten socket timeout to detect quick failure
                original_timeout = self.comfortsock.gettimeout()
                self.comfortsock.settimeout(5)

                probe = self.comfortsock.recv(1)

                if probe:
                    #logger.info("Keepalive probe succeeded on attempt %d.", attempt)
                    # Restore original timeout and exit successfully
                    self.comfortsock.settimeout(original_timeout)
                    return
                else:
                    logger.warning("Keepalive probe empty on attempt %d.", attempt)

            except (socket.timeout, socket.error) as e:
                #logger.warning("Keepalive probe failed on attempt %d: %s", attempt, e)
                dummy_var = 1   # Not used, just to avoid unused variable error.

            finally:
                # Restore original timeout after each attempt
                self.comfortsock.settimeout(original_timeout)

            # If not last attempt, wait a little before retrying
            if attempt < max_attempts:
                #logger.debug("Waiting %d seconds before next keepalive attempt.", delay_between_attempts)
                time.sleep(delay_between_attempts)

        # If we reach here, all attempts failed
        #logger.error("All %d keepalive attempts failed. Marking socket as dead.", max_attempts)
        raise socket.error(f"Socket unresponsive after {max_attempts} keepalive attempts.")

    def readlines(self, recv_buffer=BUFFER_SIZE, delim='\r'):
        """Reads lines from the Comfort socket, sending cc00 Comfort keepalive on timeout."""
        global FIRST_LOGIN
        global SAVEDTIME
        global device_properties
        global COMFORTCONNECTED

        buffer = ''
        data = True
        while data:
            try:
                data = self.comfortsock.recv(recv_buffer).decode()
            except socket.timeout as e:
                #logger.debug("Socket timeout - sending keepalive...")

                try:
                    # # Send keepalive
                    # self.SendCommand("cc00")
                    # time.sleep(0.1)

                    # # Temporarily set short timeout to quickly detect dead socket
                    # self.comfortsock.settimeout(5)
                    # probe = self.comfortsock.recv(1)

                    # if not probe:
                    #     logger.error("Keepalive failed: empty response, socket dead.")
                    #     raise socket.error("Dead socket (empty probe).")

                    # # Restore normal timeout
                    # self.comfortsock.settimeout(TIMEOUT.seconds)

                    self._send_keepalive_and_check()    # Send keepalive and check socket status

                except (socket.timeout, socket.error) as err:
                    logger.error("Keepalive check failed: %s", err)
                    COMFORTCONNECTED = False
                    FIRST_LOGIN = True
                    raise
                continue

            except (socket.error, ConnectionResetError, BrokenPipeError, TimeoutError) as e:
                logger.error("Comfort connection error during recv: %s", e)
                COMFORTCONNECTED = False
                FIRST_LOGIN = True
                raise

            else:
                if len(data) == 0:
                    logger.debug('Comfort initiated disconnect (empty recv).')
                    self.SendCommand("LI")
                    FIRST_LOGIN = True
                    COMFORTCONNECTED = False

                    if BROKERCONNECTED:
                        self.publish(ALARMCONNECTEDTOPIC, "1" if COMFORTCONNECTED else "0", qos=2, retain=False)
                        device_properties['BridgeConnected'] = 1
                else:
                    # Received normal data
                    buffer += data

                    while buffer.find(delim) != -1:
                        line, buffer = buffer.split(delim, 1)
                        yield line
        return


    def SendCommand(self, command):
        global SAVEDTIME

        try:
            self.comfortsock.sendall(("\x03"+command+"\r").encode())
            #self.comfortsock.sendall((command).encode())
            SAVEDTIME = datetime.now()
            #logger.debug("Sending Command %s", command)    # Debug sent command to Comfort.
        except:
            logger.error("Error sending command")
            self.comfortsock.close()
            raise

    def login(self):
        global SAVEDTIME
        global COMFORTCONNECTED
        self.comfortsock.sendall(("\x03LI"+self.comfort_pincode+"\r").encode())
        COMFORTCONNECTED = True
        if BROKERCONNECTED:         # Check to see if Broker is connected. Is not always at this point in the startup.
            self.publish(ALARMCONNECTEDTOPIC, 1, qos=2, retain=True)
        SAVEDTIME = datetime.now()

    def readcurrentstate(self):
        
        global SAVEDTIME
        global BypassCache
        global DEVICEMAPFILE
        
        if self.connected == True:

            device_properties['CPUType'] = 'N/A'                    # Reset CPU type to default

            #get Bypassed Zones
            self.comfortsock.sendall("\x03b?00\r".encode())       # b?00 Bypassed Zones first
            SAVEDTIME = datetime.now()
            time.sleep(0.1)
            
            #get Comfort FileSystem
            self.comfortsock.sendall("\x03V?\r".encode())
            SAVEDTIME = datetime.now()
            time.sleep(0.1)
            
            #get CPU Type
            self.comfortsock.sendall("\x03u?01\r".encode())         # Get CPU type for Main board.
            SAVEDTIME = datetime.now()
            time.sleep(0.1)
                       
            # #get HW model
            self.comfortsock.sendall("\x03EL\r".encode())
            SAVEDTIME = datetime.now()
            time.sleep(0.1)

            #Used for Unique ID
            self.comfortsock.sendall("\x03UL7FF904\r".encode())
            SAVEDTIME = datetime.now()
            time.sleep(0.1)
            
            #get Mainboard Serial Number
            self.comfortsock.sendall("\x03SN01\r".encode())
            SAVEDTIME = datetime.now()
            time.sleep(0.1)
            
            self.comfortsock.sendall("\x03M?\r".encode())
            SAVEDTIME = datetime.now()
            time.sleep(0.1)
            # #get all zone input states
            self.comfortsock.sendall("\x03Z?\r".encode())       # Comfort Zones/Inputs
            SAVEDTIME = datetime.now()
            time.sleep(0.1)

            #logging.debug("Config z value: %s", str(COMFORT_RIO_INPUTS))
            #get all SCS/RIO input states
            if COMFORT_RIO_INPUTS > 0:
                self.comfortsock.sendall("\x03z?\r".encode())       # Comfort SCS/RIO Inputs
                SAVEDTIME = datetime.now()
                time.sleep(0.1)

            #get all output states
            if ALARMNUMBEROFOUTPUTS > 0:
                self.comfortsock.sendall("\x03Y?\r".encode())
                SAVEDTIME = datetime.now()
                time.sleep(0.1)

            #logging.debug("Config y value: %s", str(COMFORT_RIO_OUTPUTS))
            #get all RIO output states
            if COMFORT_RIO_OUTPUTS > 0:
                self.comfortsock.sendall("\x03y?\r".encode())       # Request/Report all SCS/RIO Outputs
                SAVEDTIME = datetime.now()
                time.sleep(0.1)

            #get all flag states
            self.comfortsock.sendall("\x03f?00\r".encode())
            SAVEDTIME = datetime.now()
            time.sleep(0.1)
            #get Alarm Status Information
            self.comfortsock.sendall("\x03S?\r".encode())       # S? Status Request
            SAVEDTIME = datetime.now()
            time.sleep(0.1)
            #get Alarm Additional Information
            self.comfortsock.sendall("\x03a?\r".encode())       # a? Status Request - For Future Use !!!
            SAVEDTIME = datetime.now()
            time.sleep(0.1)

            #get all sensor values. 0 - 31
            self.comfortsock.sendall("\x03r?010010\r".encode())
            SAVEDTIME = datetime.now()
            time.sleep(0.1)
            self.comfortsock.sendall("\x03r?011010\r".encode())
            SAVEDTIME = datetime.now()
            time.sleep(0.1)

            #get all counter values
            for i in range(0, int((ALARMNUMBEROFCOUNTERS+1) / 16)):          # Counters 0 to 254 Using 256/16 = 16 iterations
                if i == 15:
                    self.comfortsock.sendall("\x03r?00%X00F\r".encode() % (i))
                else:
                    self.comfortsock.sendall("\x03r?00%X010\r".encode() % (i))
                SAVEDTIME = datetime.now()
                time.sleep(0.1)
            
            self.publish(ALARMAVAILABLETOPIC, 1,qos=2,retain=True)
            time.sleep(0.1)
            self.publish(ALARMLWTTOPIC, 'Online',qos=2,retain=True)
            time.sleep(0.1)
            self.publish(ALARMMESSAGETOPIC, "",qos=2,retain=True)       # Emptry string removes topic.
            time.sleep(0.1)

            device_properties['BatteryVoltageMain'] = "-1"
            device_properties['BatteryVoltageSlave1'] = "-1"
            device_properties['BatteryVoltageSlave2'] = "-1"
            device_properties['BatteryVoltageSlave3'] = "-1"
            device_properties['BatteryVoltageSlave4'] = "-1"
            device_properties['BatteryVoltageSlave5'] = "-1"
            device_properties['BatteryVoltageSlave6'] = "-1"
            device_properties['BatteryVoltageSlave7'] = "-1"
            device_properties['ChargeVoltageMain'] = "-1"
            device_properties['ChargeVoltageSlave1'] = "-1"
            device_properties['ChargeVoltageSlave2'] = "-1"
            device_properties['ChargeVoltageSlave3'] = "-1"
            device_properties['ChargeVoltageSlave4'] = "-1"
            device_properties['ChargeVoltageSlave5'] = "-1"
            device_properties['ChargeVoltageSlave6'] = "-1"
            device_properties['ChargeVoltageSlave7'] = "-1"
            device_properties['ChargerStatus'] = "N/A"
            device_properties['BatteryStatus'] = "N/A"

            if BROKERCONNECTED and COMFORTCONNECTED:
                self.publish(ALARMCONNECTEDTOPIC, 1,qos=2,retain=True)
                time.sleep(0.1)
                self.UpdateBatteryStatus()

    def UpdateBatteryStatus(self):
        global device_properties

        discoverytopic = DOMAIN + "/alarm/battery_status"
        MQTT_MSG=json.dumps({"BatteryStatus": str(device_properties['BatteryStatus']),
                             "DCSupplyStatus": str(device_properties['ChargerStatus']),
                             "BatteryMain": str(device_properties['BatteryVoltageMain']),
                             "BatterySlave1": str(device_properties['BatteryVoltageSlave1']),
                             "BatterySlave2": str(device_properties['BatteryVoltageSlave2']),
                             "BatterySlave3": str(device_properties['BatteryVoltageSlave3']),
                             "BatterySlave4": str(device_properties['BatteryVoltageSlave4']),
                             "BatterySlave5": str(device_properties['BatteryVoltageSlave5']),
                             "BatterySlave6": str(device_properties['BatteryVoltageSlave6']),
                             "BatterySlave7": str(device_properties['BatteryVoltageSlave7']),
                             "DCSupplyMain": str(device_properties['ChargeVoltageMain']),
                             "DCSupplySlave1": str(device_properties['ChargeVoltageSlave1']),
                             "DCSupplySlave2": str(device_properties['ChargeVoltageSlave2']),
                             "DCSupplySlave3": str(device_properties['ChargeVoltageSlave3']),
                             "DCSupplySlave4": str(device_properties['ChargeVoltageSlave4']),
                             "DCSupplySlave5": str(device_properties['ChargeVoltageSlave5']),
                             "DCSupplySlave6": str(device_properties['ChargeVoltageSlave6']),
                             "DCSupplySlave7": str(device_properties['ChargeVoltageSlave7']),
                             "InstalledSlaves": int(device_properties['sem_id'])
                            })
        self.publish(discoverytopic, MQTT_MSG,qos=2,retain=False)
        time.sleep(0.1)

    def UpdateDeviceInfo(self, _file = False):

        global device_properties
        global models
        global COMFORTCONNECTED
        global ADDON_VERSION
        global ALPINE_VERSION
        global COMFORT_BATTERY_STATUS_ID
        global ADDON_SLUG
        global file_exists

        #option = parser.parse_args()
        #COMFORT_BATTERY_STATUS_ID=option.comfort_battery_update
        
        file_exists = _file
  
        if ADDON_SLUG.strip() == "":
            MQTT_DEVICE = { "name": "Comfort2MQTT Bridge",
                            "identifiers": ["comfort2mqtt_bridge"],
                            "manufacturer": "Ingo de Jager",
                            "sw_version": ADDON_VERSION,
                            "hw_version": "Alpine Linux " + ALPINE_VERSION,
                            "model": "Comfort MQTT Bridge"
                        }
        else:
            MQTT_DEVICE = { "name": "Comfort2MQTT Bridge",
                            "identifiers": ["comfort2mqtt_bridge"],
                            "manufacturer": "Ingo de Jager",
                            "sw_version": ADDON_VERSION,
                            "hw_version": "Alpine Linux " + ALPINE_VERSION,
                            "configuration_url": "homeassistant://hassio/addon/" + ADDON_SLUG + "/info",
                            "model": "Comfort MQTT Bridge"
                        }
        
        MQTT_MSG=json.dumps({"CustomerName": device_properties['CustomerName'] if file_exists else None,
                             "support_url": "https://www.cytech.biz",
                             "Reference": device_properties['Reference'] if file_exists else None,
                             "ComfortFileSystem": device_properties['ComfortFileSystem'] if file_exists else None,
                             "ComfortFirmwareType": device_properties['ComfortFirmwareType'] if file_exists else None,
                             "sw_version":str(device_properties['Version']),
                             "hw_version":str(device_properties['ComfortHardwareModel']),
                             "serial_number": device_properties['SerialNumber'],
                             "cpu_type": str(device_properties['CPUType']),
                             "InstalledSlaves": int(device_properties['sem_id']),
                             "model": models[int(device_properties['ComfortFileSystem'])] if int(device_properties['ComfortFileSystem']) in models else "Unknown",
                             "BridgeConnected": str(device_properties['BridgeConnected']),
                             "device": MQTT_DEVICE
                            })

        self.publish(DOMAIN, MQTT_MSG,qos=2,retain=True)
        time.sleep(0.1)

        discoverytopic = "homeassistant/binary_sensor/" + DOMAIN + "/bridge_status/config"
        MQTT_MSG=json.dumps({"name": "Bridge MQTT Status",
                             "unique_id": DOMAIN+"_"+discoverytopic.split('/')[3],
                             "object_id": DOMAIN+"_"+discoverytopic.split('/')[3],
                             "state_topic": DOMAIN,
                             "value_template": "{{ value_json.BridgeConnected }}",
                             "qos": "2",
                             "device_class": "connectivity",
                             "payload_on": "1",
                             "payload_off": "0",
                             "device": MQTT_DEVICE
                            })
        self.publish(discoverytopic, MQTT_MSG, qos=2, retain=True)
        time.sleep(0.1)

        availability =  [
             {
                 "topic": ALARMAVAILABLETOPIC,
                 "payload_available": "1",
                 "payload_not_available": "0"
             },
             {
                 "topic": DOMAIN,
                 "payload_available": "1",
                 "payload_not_available": "0",
                 "value_template": "{{ value_json.BridgeConnected }}"
             }
            ]
        discoverytopic = "homeassistant/button/comfort2mqtt/refresh/config"
        MQTT_MSG=json.dumps({"name": "Refresh",
                             "unique_id": DOMAIN+"_"+discoverytopic.split('/')[3],
                             "object_id": DOMAIN+"_"+discoverytopic.split('/')[3],
                             "availability": availability,
                             "availability_mode": "all",
                             "command_topic": REFRESHTOPIC,
                             "payload_available": "1",
                             "payload_not_available": "0",
                             "payload_press": COMFORT_KEY,
                             "icon":"mdi:refresh",
                             "qos": "2",
                             "device": MQTT_DEVICE
                            })
        self.publish(discoverytopic, MQTT_MSG, qos=2, retain=False)
        time.sleep(0.1)
        
        discoverytopic = "homeassistant/button/comfort2mqtt/battery_update/config"
        MQTT_MSG=json.dumps({"name": "Battery Update",
                             "unique_id": DOMAIN+"_"+discoverytopic.split('/')[3],
                             "object_id": DOMAIN+"_"+discoverytopic.split('/')[3],
                             "availability": availability,
                             "availability_mode": "all",
                             "command_topic": BATTERYREFRESHTOPIC,
                             "payload_available": "1",
                             "payload_not_available": "0",
                             "payload_press": str(COMFORT_BATTERY_STATUS_ID),
                             "icon":"mdi:battery-sync-outline",
                             "qos": "2",
                             "device": MQTT_DEVICE
                            })
        if device_properties['CPUType'] != "N/A":
            self.publish(discoverytopic, MQTT_MSG, qos=2, retain=False)
            time.sleep(0.1)

        MQTT_DEVICE = { "name": models[int(device_properties['ComfortFileSystem'])] if int(device_properties['ComfortFileSystem']) in models else "Unknown",
                            "identifiers": ["comfort_device"],
                            "manufacturer":"Cytech Technology Pte Ltd.",
                            "hw_version":str(device_properties['ComfortHardwareModel']),
                            "serial_number": device_properties['SerialNumber'],
                            "sw_version":str(device_properties['Version']),
                            "model": device_properties['ComfortHardwareModel'],
                            "via_device": "comfort2mqtt_bridge"
                        }
        
        discoverytopic = "homeassistant/sensor/comfort2mqtt/comfort_state/config"
        MQTT_MSG=json.dumps({"name": "State",
                             "unique_id": discoverytopic.split('/')[3],
                             "object_id": discoverytopic.split('/')[3],
                             "state_topic": ALARMSTATUSTOPIC,
                             "availability_topic": ALARMAVAILABLETOPIC,
                             "payload_available": "1",
                             "payload_not_available": "0",
                             "icon":"mdi:shield-alert",
                             "qos": "2",
                             "native_value": "string",
                             "device": MQTT_DEVICE
                            })
        self.publish(discoverytopic, MQTT_MSG, qos=2, retain=True)
        time.sleep(0.1)

        discoverytopic = "homeassistant/sensor/comfort2mqtt/comfort_firmware/config"
        MQTT_MSG=json.dumps({"name": "Firmware",
                             "unique_id": discoverytopic.split('/')[3],
                             "object_id": discoverytopic.split('/')[3],
                             "availability_topic": ALARMAVAILABLETOPIC,
                             "payload_available": "1",
                             "payload_not_available": "0",
                             "state_topic": DOMAIN,
                             "value_template": "{{ value_json.sw_version }}",
                             "entity_category": "diagnostic",
                             "native_value": "string",
                             "icon":"mdi:chip",
                             "qos": "2",
                             "device": MQTT_DEVICE
                        })
        self.publish(discoverytopic, MQTT_MSG, qos=2, retain=False)
        time.sleep(0.1)

        discoverytopic = "homeassistant/sensor/comfort2mqtt/comfort_filesystem/config"
        MQTT_MSG=json.dumps({"name": "FileSystem",
                             "unique_id": discoverytopic.split('/')[3],
                             "object_id": discoverytopic.split('/')[3],
                             "availability_topic": ALARMAVAILABLETOPIC,
                             "payload_available": "1",
                             "payload_not_available": "0",
                             "state_topic": DOMAIN,
                             "value_template": "{{ value_json.ComfortFileSystem }}",
                             "entity_category": "diagnostic",
                             "native_value": "int",
                             "icon":"mdi:file-chart",
                             "qos": "2",
                             "device": MQTT_DEVICE
                        })
        self.publish(discoverytopic, MQTT_MSG, qos=2, retain=False)
        time.sleep(0.1)

        discoverytopic = "homeassistant/sensor/comfort2mqtt/battery_status/config"
        MQTT_MSG=json.dumps({"name": "Battery/Charger Status",
                             "unique_id": DOMAIN+"_"+discoverytopic.split('/')[3],
                             "object_id": DOMAIN+"_"+discoverytopic.split('/')[3],
                             "availability_topic": ALARMAVAILABLETOPIC,
                             "payload_available": "1",
                             "payload_not_available": "0",
                             "state_topic": DOMAIN+"/alarm/battery_status",
                             "value_template": "{{ value_json.BatteryStatus }}",
                             "json_attributes_topic": DOMAIN+"/alarm/battery_status",
                             "json_attributes_template": '''
                                {% set data = value_json %}
                                {% set slaves = data['InstalledSlaves'] %}
                                {% set ns = namespace(dict_items='') %}
                                {% for key, value in data.items() %}
                                    {% if 'BatteryMain' in key or ('BatterySlave' in key and key[-1:] | int <= slaves) %}
                                        {% if ns.dict_items %}
                                            {% set ns.dict_items = ns.dict_items + ', "' ~ key ~ '":"' ~ value ~ '"' %}
                                        {% else %}
                                            {% set ns.dict_items = '"' ~ key ~ '":"' ~ value ~ '"' %}
                                        {% endif %}
                                    {% endif %}
                                {% endfor %}
                                {% set dict_str = '{' ~ ns.dict_items ~ '}' %}
                                {% set result = dict_str | from_json %}
                                {{ result | tojson }}
                                ''',
                             "entity_category": "diagnostic",
                             "icon":"mdi:battery-check",
                             "qos": "2",
                             "device": MQTT_DEVICE
                        })
        if device_properties['CPUType'] != "N/A":
            self.publish(discoverytopic, MQTT_MSG, qos=2, retain=False)
            time.sleep(0.1)

        discoverytopic = "homeassistant/sensor/comfort2mqtt/charger_status/config"
        MQTT_MSG=json.dumps({"name": "DC Supply Status",
                             "unique_id": DOMAIN+"_"+discoverytopic.split('/')[3],
                             "object_id": DOMAIN+"_"+discoverytopic.split('/')[3],
                             "availability_topic": ALARMAVAILABLETOPIC,
                             "payload_available": "1",
                             "payload_not_available": "0",
                             "state_topic": DOMAIN+"/alarm/battery_status",
                             "value_template": "{{ value_json.DCSupplyStatus }}",
                             "json_attributes_topic": DOMAIN+"/alarm/battery_status",
                             "json_attributes_template": '''
                                {% set data = value_json %}
                                {% set slaves = data['InstalledSlaves'] %}
                                {% set ns = namespace(dict_items='') %}
                                {% for key, value in data.items() %}
                                    {% if 'DCSupplyMain' in key or ('DCSupplySlave' in key and key[-1:] | int <= slaves) %}
                                        {% if ns.dict_items %}
                                            {% set ns.dict_items = ns.dict_items + ', "' ~ key ~ '":"' ~ value ~ '"' %}
                                        {% else %}
                                            {% set ns.dict_items = '"' ~ key ~ '":"' ~ value ~ '"' %}
                                        {% endif %}
                                    {% endif %}
                                {% endfor %}
                                {% set dict_str = '{' ~ ns.dict_items ~ '}' %}
                                {% set result = dict_str | from_json %}
                                {{ result | tojson }}
                                ''',
                             "entity_category": "diagnostic",
                             "icon":"mdi:battery-charging",
                             "qos": "2",
                             "device": MQTT_DEVICE
                        })
        if device_properties['CPUType'] != "N/A":
            self.publish(discoverytopic, MQTT_MSG, qos=2, retain=False)
            time.sleep(0.1)
            #logging.debug(MQTT_MSG)

        discoverytopic = "homeassistant/sensor/comfort2mqtt/comfort_bypass_zones/config"
        MQTT_MSG=json.dumps({"name": "Bypassed Zones",
                             "unique_id": discoverytopic.split('/')[3],
                             "object_id": discoverytopic.split('/')[3],
                             "state_topic": ALARMBYPASSTOPIC,
                             "availability_topic": ALARMAVAILABLETOPIC,
                             "payload_available": "1",
                             "payload_not_available": "0",
                             "icon":"mdi:shield-remove",
                             "qos": "2",
                             "native_value": "string",
                             "device": MQTT_DEVICE
                            })
        self.publish(discoverytopic, MQTT_MSG, qos=2, retain=False)
        time.sleep(0.1)

        #Mode_Description = {0:"Disarmed", 1:"Away Mode", 2:"Night Mode", 3:"Day Mode", 4:"Vacation Mode"}
        discoverytopic = "homeassistant/sensor/comfort2mqtt/comfort_mode/config"
        MQTT_MSG=json.dumps({"name": "Mode",
                             "unique_id": DOMAIN+"_"+discoverytopic.split('/')[3],
                             "object_id": DOMAIN+"_"+discoverytopic.split('/')[3],
                             "availability_topic": ALARMAVAILABLETOPIC,
                             "payload_available": "1",
                             "payload_not_available": "0",
                             "state_topic": ALARMMODETOPIC,
                             "icon":"mdi:home",
                             "device": MQTT_DEVICE
                        })
        self.publish(discoverytopic, MQTT_MSG, qos=2, retain=True)
        time.sleep(0.1)

        discoverytopic = "homeassistant/sensor/comfort2mqtt/comfort_customername/config"
        MQTT_MSG=json.dumps({"name": "Customer Name",
                             "unique_id": discoverytopic.split('/')[3],
                             "object_id": discoverytopic.split('/')[3],
                             "availability_topic": ALARMAVAILABLETOPIC,
                             "payload_available": "1",
                             "payload_not_available": "0",
                             "state_topic": DOMAIN,
                             "value_template": "{{ value_json.CustomerName }}",
                             "entity_category": "diagnostic",
                             "native_value": "string",
                             "icon":"mdi:shield-account",
                             "qos": "2",
                             "device": MQTT_DEVICE
                            })
        self.publish(discoverytopic, MQTT_MSG, qos=2, retain=False)
        time.sleep(0.1)

        discoverytopic = "homeassistant/sensor/comfort2mqtt/comfort_reference/config"
        MQTT_MSG=json.dumps({"name": "Reference",
                             "unique_id": discoverytopic.split('/')[3],
                             "object_id": discoverytopic.split('/')[3],
                             "availability_topic": ALARMAVAILABLETOPIC,
                             "payload_available": "1",
                             "payload_not_available": "0",
                             "state_topic": DOMAIN,
                             "value_template": "{{ value_json.Reference }}",
                             "entity_category": "diagnostic",
                             "native_value": "string",
                             "icon":"mdi:home-circle",
                             "qos": "2",
                             "device": MQTT_DEVICE
                            })
        self.publish(discoverytopic, MQTT_MSG, qos=2, retain=False)
        time.sleep(0.1)
        
        discoverytopic = "homeassistant/sensor/comfort2mqtt/comfort_serial_number/config"
        MQTT_MSG=json.dumps({"name": "Serial Number",
                             "unique_id": discoverytopic.split('/')[3],
                             "object_id": discoverytopic.split('/')[3],
                             "availability_topic": ALARMAVAILABLETOPIC,
                             "payload_available": "1",
                             "payload_not_available": "0",
                             "state_topic": DOMAIN,
                             "value_template": "{{ value_json.serial_number }}",
                             "entity_category": "diagnostic",
                             "native_value": "string",
                             "icon":"mdi:numeric",
                             "qos": "2",
                             "device": MQTT_DEVICE
                            })
        self.publish(discoverytopic, MQTT_MSG, qos=2, retain=False)
        time.sleep(0.1)


        discoverytopic = "homeassistant/binary_sensor/comfort2mqtt/comfort_connection_state/config"
        MQTT_MSG=json.dumps({"name": "LAN Status",
                             "object_id": discoverytopic.split('/')[3],
                             "unique_id": discoverytopic.split('/')[3],
                             "state_topic": ALARMCONNECTEDTOPIC,
                             "device_class": "connectivity",
                             "entity_category": "diagnostic",
                             "payload_off": "0",
                             "payload_on": "1",
                             "qos": "2",
                             "device": MQTT_DEVICE
                            })
        self.publish(discoverytopic, MQTT_MSG, qos=2, retain=True)
        time.sleep(0.1)

    def BatteryStatus(*voltages):  # Tuple of all voltages
        for voltage in voltages:
            if voltage > 15:        # Critical Overcharge
                return "Critical"
            if voltage > 14.6:      # Overcharge
                return "Warning"
            if voltage <= 9.5:     # Discharged/Crital Charge or No Charge
                return "Critical"
            elif voltage < 11.5:   # Severely Discharged/Low Charge
                return "Warning"
        return "Ok"

#        Example usage with 5 battery voltages
#           battery_voltages = [13.0, 12.1, 12.8, 13.5, 14.2]                          # Test
#           print(battery_status(*battery_voltages))  # Output will be "Critical"      # Test
    
    def setdatetime(self):
        global SAVEDTIME
        if self.connected == True:  #set current date and time if COMFORT_TIME Flag is set to True
            if COMFORT_TIME == 'True':
                logger.info('Setting Comfort Date/Time')
                now = datetime.now()
                self.comfortsock.sendall(("\x03DT%02d%02d%02d%02d%02d%02d\r" % (now.year, now.month, now.day, now.hour, now.minute, now.second)).encode())
                SAVEDTIME = datetime.now()
                time.sleep(0.1)

    def check_string(self, s):

        pattern = re.compile(r'(\x03[a-zA-Z0-9!?]*)$')
        match = re.search(pattern, s)
    
        if match:
            return True
        else:
            return False

    def exit_gracefully(self, signum, frame):
        
        global RUN
        global SAVEDTIME
        global device_properties
        global file_exists
        global models
        
        logger.debug("SIGNUM: %s received, Shutting down.", str(signum))
        
        device_properties['BridgeConnected'] = 0
        if self.connected == True:
            self.comfortsock.sendall("\x03LI\r".encode()) #Logout command.
            SAVEDTIME = datetime.now()
            self.connected = False
        if BROKERCONNECTED == True:      # MQTT Connected
            infot = self.publish(ALARMCONNECTEDTOPIC, 0,qos=2,retain=True)
            infot = self.publish(ALARMAVAILABLETOPIC, 0,qos=2,retain=True)
            infot = self.publish(ALARMLWTTOPIC, 'Offline',qos=2,retain=True)

            if ADDON_SLUG.strip() == "":
                MQTT_DEVICE = { "name": "Comfort2MQTT Bridge",
                            "identifiers": ["comfort2mqtt_bridge"],
                            "manufacturer": "Ingo de Jager",
                            "sw_version": ADDON_VERSION,
                            "hw_version": "Alpine Linux " + ALPINE_VERSION,
                            "model": "Comfort MQTT Bridge"
                        }
            else:
                MQTT_DEVICE = { "name": "Comfort2MQTT Bridge",
                            "identifiers": ["comfort2mqtt_bridge"],
                            "manufacturer": "Ingo de Jager",
                            "sw_version": ADDON_VERSION,
                            "hw_version": "Alpine Linux " + ALPINE_VERSION,
                            "configuration_url": "homeassistant://hassio/addon/" + ADDON_SLUG + "/info",
                            "model": "Comfort MQTT Bridge"
                        }

            MQTT_MSG=json.dumps({"CustomerName": device_properties['CustomerName'] if file_exists else None,
                             "support_url": "https://www.cytech.biz",
                             "Reference": device_properties['Reference'] if file_exists else None,
                             "ComfortFileSystem": device_properties['ComfortFileSystem'] if file_exists else None,
                             "ComfortFirmwareType": device_properties['ComfortFirmwareType'] if file_exists else None,
                             "sw_version":str(device_properties['Version']),
                             "hw_version":str(device_properties['ComfortHardwareModel']),
                             "serial_number": device_properties['SerialNumber'],
                             "cpu_type": str(device_properties['CPUType']),
                             "InstalledSlaves": int(device_properties['sem_id']),
                             "model": models[int(device_properties['ComfortFileSystem'])] if int(device_properties['ComfortFileSystem']) in models else "Unknown",
                             "BridgeConnected": str(device_properties['BridgeConnected']),
                             "device": MQTT_DEVICE
                            })
            infot = self.publish(DOMAIN, MQTT_MSG,qos=2,retain=False)
            infot.wait_for_publish()

            discoverytopic = DOMAIN + "/alarm/battery_status"
            MQTT_MSG=json.dumps({"BatteryStatus": str(device_properties['BatteryStatus']),
                             "DCSupplyStatus": str(device_properties['ChargerStatus']),
                             "BatteryMain": str(device_properties['BatteryVoltageMain']),
                             "BatterySlave1": str(device_properties['BatteryVoltageSlave1']),
                             "BatterySlave2": str(device_properties['BatteryVoltageSlave2']),
                             "BatterySlave3": str(device_properties['BatteryVoltageSlave3']),
                             "BatterySlave4": str(device_properties['BatteryVoltageSlave4']),
                             "BatterySlave5": str(device_properties['BatteryVoltageSlave5']),
                             "BatterySlave6": str(device_properties['BatteryVoltageSlave6']),
                             "BatterySlave7": str(device_properties['BatteryVoltageSlave7']),
                             "DCSupplyMain": str(device_properties['ChargeVoltageMain']),
                             "DCSupplySlave1": str(device_properties['ChargeVoltageSlave1']),
                             "DCSupplySlave2": str(device_properties['ChargeVoltageSlave2']),
                             "DCSupplySlave3": str(device_properties['ChargeVoltageSlave3']),
                             "DCSupplySlave4": str(device_properties['ChargeVoltageSlave4']),
                             "DCSupplySlave5": str(device_properties['ChargeVoltageSlave5']),
                             "DCSupplySlave6": str(device_properties['ChargeVoltageSlave6']),
                             "DCSupplySlave7": str(device_properties['ChargeVoltageSlave7']),
                             "InstalledSlaves": int(device_properties['sem_id'])
                            })
            infot = self.publish(discoverytopic, MQTT_MSG,qos=2,retain=False)
            infot.wait_for_publish()

        RUN = False
        exit(0)

    def add_descriptions(self, file):    # Checks optional object description files and populate dictionaries accordingly.

        global ZONEMAPFILE
        global COUNTERMAPFILE
        global FLAGMAPFILE
        global OUTPUTMAPFILE
        global SENSORMAPFILE
        global SCSRIOMAPFILE
        global DEVICEMAPFILE
        global USERMAPFILE

        global input_properties
        global counter_properties
        global flag_properties
        global output_properties
        global sensor_properties
        global scsrio_properties
        global device_properties
        global user_properties
        
        if file.is_file():
            file_stats = os.stat(file)
            logger.info ("Comfigurator (CCLX) File detected, %s Bytes", file_stats.st_size)
            tree = ET.parse(file)
            root = tree.getroot()

            input_properties = {}
            counter_properties = {}
            flag_properties = {}
            output_properties = {}
            sensor_properties = {}
            scsrio_properties = {}
            user_properties = {}

            for entry in root.iter('ConfigInfo'):
                CustomerName = None
                Reference = None
                #UcmVersion = None
                #UcmRevision = None
                ComfortFileSystem = None
                ComfortFirmware = None

                CustomerName = entry.attrib.get('CustomerName')[:200] if entry.attrib.get('CustomerName') else None          # Limit to 200 characters
                Reference = entry.attrib.get('Reference')[:200] if entry.attrib.get('Reference') else None                 # Limit to 200 characters
                #UcmVersion = entry.attrib.get('UcmVersion')
                #UcmRevision = entry.attrib.get('UcmRevision')
                ComfortFileSystem = entry.attrib.get('ComfortFileSystem')[:2] if entry.attrib.get('ComfortFileSystem') else None   # Limit to 2 characters
                ComfortFirmware = entry.attrib.get('ComfortFirmwareType')  
                device_properties['CustomerName'] = CustomerName
                device_properties['Reference'] = Reference
                device_properties['ComfortFileSystem'] = ComfortFileSystem
                device_properties['ComfortFirmwareType'] = ComfortFirmware
                device_properties['CPUType'] = "N/A"
  
                DEVICEMAPFILE = True

            for zone in root.iter('Zone'):
                name = ''
                number = ''
                virtualinput = ''
                ZoneWord1 = ''
                ZoneWord2 = ''
                ZoneWord3 = ''
                ZoneWord4 = ''
                ZoneWord = ''
                name = zone.attrib.get('Name')[:16] if zone.attrib.get('Name') else ''
                number = zone.attrib.get('Number')[:3] if zone.attrib.get('Number') else ''
                virtualinput = zone.attrib.get('VirtualInput')[:5] if zone.attrib.get('VirtualInput') else ''
                ZoneWord1 = zone.attrib.get('ZoneWord1')[:16] if zone.attrib.get('ZoneWord1') else ''
                if ZoneWord1 != None: ZoneWord = ZoneWord1
                ZoneWord2 = zone.attrib.get('ZoneWord2')[:16] if zone.attrib.get('ZoneWord2') else ''
                if ZoneWord2 != None: ZoneWord = ZoneWord + " " +ZoneWord2
                ZoneWord3 = zone.attrib.get('ZoneWord3')[:16] if zone.attrib.get('ZoneWord3') else ''
                if ZoneWord3 != None: ZoneWord = ZoneWord + " " +ZoneWord3
                ZoneWord4 = zone.attrib.get('ZoneWord4')[:16] if zone.attrib.get('ZoneWord4') else ''
                if ZoneWord4 != None: ZoneWord = ZoneWord + " " +ZoneWord4

                if self.CheckIndexNumberFormat(number):
                    ZONEMAPFILE = True               
                else:
                    number = ''
                    logger.error("Invalid Zone Number detected in '%s'.", file)
                    ZONEMAPFILE = False
                    break
                if self.CheckZoneNameFormat(name): 
                    ZONEMAPFILE = True              
                else:
                    name = ''
                    logger.error("Invalid Zone Name detected in '%s'.", file)
                    ZONEMAPFILE = False             
                    break

                # Add the truncated value to the dictionary
                inner_dict = {}
                inner_dict['Name'] = name
                inner_dict['ZoneWord'] = ZoneWord.strip()
                inner_dict['VirtualInput'] = virtualinput
                input_properties[number] = inner_dict
                
            for counter in root.iter('Counter'):
                name = ''
                number = ''
                name = counter.attrib.get('Name')[:16] if counter.attrib.get('Name') else ''
                number = counter.attrib.get('Number')[:3] if counter.attrib.get('Number') else ''

                if self.CheckIndexNumberFormat(number):
                    COUNTERMAPFILE = True               
                else:
                    number = ''
                    logger.error("Invalid Counter Number detected in '%s'.", file)
                    COUNTERMAPFILE = False
                    break
                if self.CheckZoneNameFormat(name): 
                    COUNTERMAPFILE = True              
                else:
                    name = ''
                    logger.error("Invalid Counter Name detected in '%s'.", file)
                    COUNTERMAPFILE = False             
                    break

                # Add the truncated value to the dictionary
                counter_properties[number] = name

            for flag in root.iter('Flag'):
                name = ''
                number = ''
                name = flag.attrib.get('Name')[:16] if flag.attrib.get('Name') else ''
                number = flag.attrib.get('Number')[:3] if flag.attrib.get('Number') else ''

                if self.CheckIndexNumberFormat(number):
                    FLAGMAPFILE = True               
                else:
                    number = ''
                    logger.error("Invalid Flag Number detected in '%s'.", file)
                    FLAGMAPFILE = False
                    break
                if self.CheckZoneNameFormat(name): 
                    FLAGMAPFILE = True              
                else:
                    name = ''
                    logger.error("Invalid Flag Name detected in '%s'.", file)
                    FLAGMAPFILE = False             
                    break

                # Add the truncated value to the dictionary
                flag_properties[number] = name

            for output in root.iter('Output'):
                name = ''
                number = ''
                name = output.attrib.get('Name')[:16] if output.attrib.get('Name') else ''
                number = output.attrib.get('Number')[:3] if output.attrib.get('Number') else ''

                if self.CheckIndexNumberFormat(number):
                    OUTPUTMAPFILE = True               
                else:
                    number = ''
                    logger.error("Invalid Output Number detected in '%s'.", file)
                    OUTPUTMAPFILE = False
                    break
                if self.CheckZoneNameFormat(name): 
                    OUTPUTMAPFILE = True              
                else:
                    name = ''
                    logger.error("Invalid Output Name detected in '%s'.", file)
                    OUTPUTMAPFILE = False             
                    break

                # Add the truncated value to the dictionary
                output_properties[number] = name

            for sensor in root.iter('SensorResponse'):
                name = ''
                number = ''
                name = sensor.attrib.get('Name')[:16] if sensor.attrib.get('Name') else ''
                number = sensor.attrib.get('Number')[:3] if sensor.attrib.get('Number') else ''

                if self.CheckIndexNumberFormat(number):
                    SENSORMAPFILE = True               
                else:
                    number = ''
                    logger.error("Invalid Sensor Number detected in '%s'.", file)
                    SENSORMAPFILE = False
                    break
                if self.CheckZoneNameFormat(name): 
                    SENSORMAPFILE = True              
                else:
                    name = ''
                    logger.error("Invalid Sensor Name detected in '%s'.", file)
                    SENSORMAPFILE = False             
                    break

                # Add the truncated value to the dictionary
                sensor_properties[number] = name

            for scsrio in root.iter('ScsRioResponse'):
                name = ''
                number = ''
                name = scsrio.attrib.get('Name')[:16] if scsrio.attrib.get('Name') else ''
                number = scsrio.attrib.get('Number')[:3] if scsrio.attrib.get('Number') else ''

                if self.CheckIndexNumberFormat(number):
                    SCSRIOMAPFILE = True               
                else:
                    number = ''
                    logger.error("Invalid SCS/RIO Number detected in '%s'.", file)
                    SCSRIOMAPFILE = False
                    break
                if self.CheckZoneNameFormat(name): 
                    SCSRIOMAPFILE = True              
                else:
                    name = ''
                    logger.error("Invalid SCS/RIO Name detected in '%s'.", file)
                    SCSRIOMAPFILE = False             
                    break

                # Add the truncated value to the dictionary
                scsrio_properties[number] = name

            for user in root.iter('Authorisation'):
                name = ''
                number = ''
                name = user.attrib.get('Name')[:16] if user.attrib.get('Name') else ''
                number = user.attrib.get('Number')[:3] if user.attrib.get('Number') else ''

                if self.CheckIndexNumberFormat(number):
                    USERMAPFILE = True               
                else:
                    number = ''
                    logger.error("Invalid User Number detected in '%s'.", file)
                    USERMAPFILE = False
                    break
                if self.CheckZoneNameFormat(name): 
                    USERMAPFILE = True              
                else:
                    name = ''
                    logger.error("Invalid User Name detected in '%s'.", file)
                    USERMAPFILE = False             
                    break

                # Add the truncated value to the dictionary
                user_properties[number] = name
        else:
            device_properties['CustomerName'] = None
            device_properties['Reference'] = None
            device_properties['Version'] = None
            device_properties['ComfortFileSystem'] = None
            device_properties['ComfortFirmwareType'] = None
            
            logger.info ("Comfigurator (CCLX) File Not Found")
        
        device_properties['uid'] = None

        return file
    
    def sanitize_filename(self, input_string, valid_extensions=None):     # Thanks ChatGPT :-)
        """
        Sanitize the input filename string to ensure it is a valid filename with an extension,
        and prevent directory tree walking.

        :param input_string: The user input string to sanitize.
        :param valid_extensions: List of valid extensions (e.g., ['cclx']). None to allow any extension.
        :return: A sanitized filename or None if invalid.
        """
        # Define a regular expression pattern for a valid filename (alphanumeric and specific special characters)
        valid_filename_pattern = r'^[\w\-. ]+$'  # Alphanumeric characters, underscores, hyphens and dots. Spaces (for future development)
    
        # Split the filename and extension
        base, ext = os.path.splitext(input_string)
    
        # Check if the base name is valid
        if not re.match(valid_filename_pattern, base):
            return None
    
        # Validate the extension if a list of valid extensions is provided
        if valid_extensions:
            ext = ext.lstrip('.').lower()
            if ext not in valid_extensions:
                return None
    
        # Join the base and extension back
        sanitized_filename = f"{base}.{ext}" if ext else base
        #sanitized_filename = f"\"{base}.{ext}\"" if ext else base
    
        # Ensure no directory traversal characters are present
        if '..' in sanitized_filename or '/' in sanitized_filename or '\\' in sanitized_filename:
            return None
    
        #logging.debug("Sanitized Filename: %s", sanitized_filename)
        return sanitized_filename

    def run(self):

        global FIRST_LOGIN         # Used to track if Addon started up or not.
        global RUN
        global SAVEDTIME
        global TIMEOUT
        global BROKERCONNECTED
        global COMFORTCONNECTED
        global COMFORT_SERIAL
        global COMFORT_KEY
        
        global ZONEMAPFILE
        global COUNTERMAPFILE
        global FLAGMAPFILE
        global OUTPUTMAPFILE
        global SENSORMAPFILE
        global SCSRIOMAPFILE
        global DEVICEMAPFILE
        global USERMAPFILE

        global input_properties
        global counter_properties
        global flag_properties
        global output_properties
        global sensor_properties
        global scsrio_properties
        global device_properties
        global user_properties

        global ZoneCache
        global BypassCache
        global CacheState
        global models
        global SupportedFirmware

        global ALARMSTATE

        signal.signal(signal.SIGTERM, self.exit_gracefully)
        if os.name != 'nt':
            signal.signal(signal.SIGQUIT, self.exit_gracefully)
           
        if COMFORT_CCLX_FILE != None:
            config_filename = self.sanitize_filename(COMFORT_CCLX_FILE,'cclx')
            if config_filename:
                #logging.debug ("/config/" + config_filename)
                self.add_descriptions(Path("/config/" + config_filename))
            else:
                logging.info("Illegal Comfigurator CCLX file detected, no enrichment will be loaded.")
        else:
            logging.info("No Comfigurator CCLX file found, no enrichment will be loaded.")
        
        self.connect_async(self.mqtt_ip, self.mqtt_port, 60)
        if self.connected == True:
            BROKERCONNECTED = True
            device_properties['BridgeConnected'] = 1
            self.publish(ALARMAVAILABLETOPIC, 0,qos=2,retain=True)
            self.will_set(ALARMLWTTOPIC, payload="Offline", qos=2, retain=True)

        self.loop_start()   

        try:
            while RUN:
                self.comfortsock = None     # Added 29/4/2025
                try:
                    self.comfortsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.comfortsock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    self.comfortsock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 10)   # Start keepalive after 10s of inactivity
                    self.comfortsock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 5)   # Interval between keepalive probes
                    self.comfortsock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)     # Number of failed probes before disconnect

                    logger.info('Connecting to Comfort (%s) on port %s', self.comfort_ip, str(self.comfort_port) )
                    self.comfortsock.connect((self.comfort_ip, self.comfort_port))
                    self.comfortsock.settimeout(TIMEOUT.seconds)
                    self.login()

                    SAVEDTIME = datetime.now()      # Added 29/4/2025

                    for line in self.readlines():

                        pattern = re.compile(r'(\x03[a-zA-Z0-9!?]*)$')      # Extract 'legal' characters from line.
                        match = re.search(pattern, line)
                        if match:
                            line = match.group(1)
                        else:
                            continue

                        if line[1:] != "cc00": #and not line[1:].startswith("D?00"):      # D?00 replies might not be used - wait Cytech command inclusion.
                            logger.debug(line[1:])  	    # Print all responses in DEBUG mode only. Print all received Comfort commands except keepalives.

                            if datetime.now() > SAVEDTIME + TIMEOUT:            #
                                self.comfortsock.sendall("\x03cc00\r".encode()) #echo command for keepalive
                                SAVEDTIME = datetime.now()
                                time.sleep(0.1)

                        if self.check_string(line):         # Check for "(\x03[a-zA-Z0-9]*)$" in complete line. Might be redundant as same check done above.
                            pattern = re.compile(r'(\x03[a-zA-Z0-9!?]*)$')      # Extract 'legal' characters from line.
                            match = re.search(pattern, line)

                            if match:
                                line = match.group(1)
                            else:
                                continue

                            if line[1:3] == "LU":
                                luMsg = ComfortLUUserLoggedIn(line[1:])
                                if luMsg.user != 0:
                                    logger.info('Comfort Login Ok - User %s', (luMsg.user if luMsg.user != 254 else 'Engineer'))

                                    if BROKERCONNECTED == True:     # Settle time for Comfort.
                                        time.sleep(1)
                                    else:
                                        logger.info("Waiting for MQTT Broker to come Online...")

                                    self.connected = True  
                                    self.publish(ALARMCOMMANDTOPIC, "comm test", qos=2,retain=True)
                                    time.sleep(0.01)
                                    self.publish(REFRESHTOPIC, "", qos=2,retain=True)               # Clear Refresh Key
                                    time.sleep(0.01)

                                    self.setdatetime()      # Set Date/Time if Option is enabled

                                    if FIRST_LOGIN == True:
                                        self.readcurrentstate()
                                        FIRST_LOGIN = False
                                else:
                                    logger.debug("Disconnect (LU00) Received from Comfort.")
                                    FIRST_LOGIN = True
                                    COMFORTCONNECTED = False
                                    if BROKERCONNECTED == True:      # MQTT Connected ??
                                        self.publish(ALARMAVAILABLETOPIC, 0,qos=2,retain=True)
                                        self.publish(ALARMLWTTOPIC, 'Offline',qos=2,retain=True)
                                        self.publish(ALARMCONNECTEDTOPIC, "0", qos=2, retain=False)
                                    break

                            elif line[1:5] == "PS00":       # Set Date/Time once a day on receipt of PS command. Usually midnight or any time the system is armed.
                                self.setdatetime()          # Set Date/Time if Flag is set at 00:00 every day if option is enabled.

                            elif line[1:3] == "IP" and CacheState:
                                ipMsg = ComfortIPInputActivationReport(line[1:])
                                if ipMsg.state < 2 and CacheState:
                                    _time = datetime.now().replace(microsecond=0).isoformat()
                                    
                                    if ipMsg.input <= 128:
                                        try:
                                            _name = input_properties[str(ipMsg.input)]['Name'] if ZONEMAPFILE else "Zone" + "{:02d}".format(ipMsg.input)
                                        except KeyError as e:
                                            _name = "Zone" + str(ipMsg.input)
                                        try:
                                            _zoneword = input_properties[str(ipMsg.input)]['ZoneWord'] if ZONEMAPFILE else ""
                                        except KeyError as e:
                                            _zoneword = ""
                                    else:
                                        try:
                                            _name = scsrio_properties[str(ipMsg.input)] if SCSRIOMAPFILE else "ScsRioResp" + str(ipMsg.input)
                                        except KeyError as e:
                                            _name = "ScsRioResp" + str(ipMsg.input)
                                        _zoneword = None
                                    ZoneCache[ipMsg.input] = ipMsg.state           # Update local ZoneCache
                                    MQTT_MSG=json.dumps({"Time": _time, 
                                                         "Name": _name, 
                                                         "ZoneWord": _zoneword if ipMsg.input <= 128 else None,
                                                         "State": ipMsg.state,
                                                         "Bypass": BypassCache[ipMsg.input] if ipMsg.input <= 128 else None
                                                        })
                                    if ipMsg.input <= int(COMFORT_INPUTS) or ipMsg.input > 128:
                                        self.publish(ALARMINPUTTOPIC % ipMsg.input, MQTT_MSG,qos=2,retain=False)    # 19/8/2024 Changed to False
                                        time.sleep(0.01)

                            elif line[1:3] == "CT" and CacheState:
                                ipMsgCT = ComfortCTCounterActivationReport(line[1:])
                                _time = datetime.now().replace(microsecond=0).isoformat()
                                _name = counter_properties[str(ipMsgCT.counter)] if COUNTERMAPFILE else "counter" + str(ipMsgCT.counter)
                                MQTT_MSG=json.dumps({"Time": _time, 
                                                     "Name": _name, 
                                                     "Value": ipMsgCT.value,
                                                     "State": ipMsgCT.state
                                                    })
                                self.publish(ALARMCOUNTERINPUTRANGE % ipMsgCT.counter, MQTT_MSG,qos=2,retain=False)    # 19/8/2024 Changed to False
                                time.sleep(0.01)

                            elif line[1:3] == "s?":
                                ipMsgSQ = ComfortCTCounterActivationReport(line[1:])
                                self.publish(ALARMSENSORTOPIC % ipMsgSQ.counter, ipMsgSQ.state, qos=2, retain=False)

                            elif line[1:3] == "sr" and CacheState:
                                ipMsgSR = ComfortCTCounterActivationReport(line[1:])
                                _time = datetime.now().replace(microsecond=0).isoformat()
                                _name = sensor_properties[str(ipMsgSR.counter)] if SENSORMAPFILE else "Sensor" + "{:02d}".format(ipMsgSR.counter)
                                MQTT_MSG=json.dumps({"Time": _time, 
                                                     "Name": _name,
                                                     "Value": ipMsgSR.value
                                                    })
                                self.publish(ALARMSENSORTOPIC % ipMsgSR.counter, MQTT_MSG,qos=2,retain=False)    # 19/8/2024 Changed to False

                            elif line[1:3] == "Z?":                             # Zones/Inputs
                                zMsg = ComfortZ_ReportAllZones(line[1:])
                                for ipMsgZ in zMsg.inputs:
                                    _time = datetime.now().replace(microsecond=0).isoformat()
                                    try:
                                        _name = input_properties[str(ipMsgZ.input)]['Name'] if ZONEMAPFILE else "Zone" + str(ipMsgZ.input)
                                    except KeyError as e:
                                        # Only print error is zone is in configured range
                                        if int(e.args[0]) <= ALARMNUMBEROFOUTPUTS:
                                            logging.debug ("Zone %s not in CCLX file, ignoring CCLX 'Name' and 'ZoneWord' enrichment", str(e))
                                        _name = "Zone" + str(ipMsgZ.input)
                                    try:
                                        _zoneword = input_properties[str(ipMsgZ.input)]['ZoneWord'] if ZONEMAPFILE else ""
                                    except KeyError as e:
                                        _zoneword = ""

                                    ZoneCache[ipMsgZ.input] = ipMsgZ.state           # Update local ZoneCache
                                    MQTT_MSG=json.dumps({"Time": _time, 
                                                         "Name": _name, 
                                                         "ZoneWord": _zoneword,
                                                         "State": ipMsgZ.state,
                                                         "Bypass": BypassCache[ipMsgZ.input]
                                                        })
                                    if ipMsgZ.input <= int(COMFORT_INPUTS):
                                        self.publish(ALARMINPUTTOPIC % ipMsgZ.input, MQTT_MSG,qos=2,retain=False)
                                    else:
                                        self.publish(ALARMINPUTTOPIC % ipMsgZ.input, "",qos=2,retain=False)
                                    time.sleep(0.01)    # 10mS delay between commands
                                logger.debug("Max. Reported Zones/Inputs: %d", zMsg.max_zones)
                                if zMsg.max_zones < int(COMFORT_INPUTS):
                                    logger.warning("Max. Reported Zone Inputs of %d is less than the configured value of %s", zMsg.max_zones, COMFORT_INPUTS)

                            elif line[1:3] == "z?":                             # SCS/RIO Inputs
                                zMsg = Comfort_Z_ReportAllZones(line[1:])
                                for ipMsgZ in zMsg.inputs:
                                    _time = datetime.now().replace(microsecond=0).isoformat()
                                    try:
                                        _name = scsrio_properties[str(ipMsgZ.input)] if SCSRIOMAPFILE else "ScsRioResp" + str(ipMsgZ.input)
                                    except KeyError as e:
                                        if int(COMFORT_RIO_INPUTS) > 0 and int(e.args[0]) < ALARMRIOINPUTRANGE[-1]:
                                            logging.debug ("SCS/RIO Input %s not in CCLX file, ignoring CCLX enrichment", str(e))
                                        _name = "ScsRioResp" + str(ipMsgZ.input)
                                    ZoneCache[ipMsgZ.input] = ipMsgZ.state           # Update local ZoneCache
                                    MQTT_MSG=json.dumps({"Time": _time, 
                                                         "Name": _name,
                                                         "ZoneWord": None,
                                                         "State": ipMsgZ.state,
                                                         "Bypass": None
                                                        })
                                    if ipMsgZ.input <= 128 + int(COMFORT_RIO_INPUTS):
                                        self.publish(ALARMINPUTTOPIC % ipMsgZ.input, MQTT_MSG,qos=2,retain=False)
                                    else:
                                        self.publish(ALARMINPUTTOPIC % ipMsgZ.input, "",qos=2,retain=False)     # Remove any previously created objects
                                    time.sleep(0.01)    # 10mS delay between commands

                                logger.debug("Max. Reported SCS/RIO Inputs: %d", zMsg.max_zones)

                            elif line[1:3] == "M?" or line[1:3] == "MD":
                                mMsg = ComfortM_SecurityModeReport(line[1:])
                                self.publish(ALARMSTATETOPIC, mMsg.modename,qos=2,retain=True)      #Disarmed, Day etc
                                self.publish(ALARMMODETOPIC, mMsg.mode,qos=2,retain=True)
                                ALARMSTATE = mMsg.mode         # Save Numerical state.
                                self.entryexitdelay = 0                         #zero out the countdown timer

                            elif line[1:3] == "S?":
                                SMsg = ComfortS_SecurityModeReport(line[1:])
                                self.publish(ALARMSTATUSTOPIC, SMsg.modename,qos=2,retain=True)     # Idle, Alert etc.
                                ALARMSTATE = SMsg.mode         # Save Numerical state.

                            elif line[1:3] == "V?":
                                VMsg = ComfortV_SystemTypeReport(line[1:])
                                                 
                                device_properties['ComfortFileSystem'] = str(VMsg.filesystem)
                                device_properties['ComfortFirmwareType'] = str(VMsg.firmware)
                                device_properties['Version'] = str(VMsg.version) + "." + str(VMsg.revision).zfill(3)

                                self.UpdateDeviceInfo(True)     # Update Device properties.
                                
                                current_firmware = float(str(VMsg.version) + "." + str(VMsg.revision).zfill(3))
                                #supported_firmware = float(SupportedFirmware)
                                #logging.info("current: %s", current_firmware)
                                #logging.info("supported: %s", float(SupportedFirmware))
                                             
                                #logging.info("%s detected (Firmware %d.%03d)", models[int(device_properties['ComfortFileSystem'])] if int(device_properties['ComfortFileSystem']) in models else "Unknown device", VMsg.version, VMsg.revision)

                                if current_firmware >= SupportedFirmware:
                                    logging.info("%s detected (Supported Firmware %d.%03d)", models[int(device_properties['ComfortFileSystem'])] if int(device_properties['ComfortFileSystem']) in models else "Unknown device", VMsg.version, VMsg.revision)
                                else:
                                    logging.error("%s detected (Unsupported Firmware %d.%03d)", models[int(device_properties['ComfortFileSystem'])] if int(device_properties['ComfortFileSystem']) in models else "Unknown device", VMsg.version, VMsg.revision)

                            elif line[1:5] == "u?01":       # Determine CPU type if available.
                                uMsg = Comfort_U_SystemCPUTypeReport(line[1:])
                                                
                                device_properties['CPUType'] = str(uMsg.cputype)
                                if str(uMsg.cputype) != "N/A":
                                    logging.debug("%s Mainboard CPU detected. Battery Monitoring Enabled.", str(device_properties['CPUType']))
                                else:   # Clear out battery voltages
                                    device_properties['BatteryVoltageMain'] = "-1"
                                    device_properties['BatteryVoltageSlave1'] = "-1"
                                    device_properties['BatteryVoltageSlave2'] = "-1"
                                    device_properties['BatteryVoltageSlave3'] = "-1"
                                    device_properties['BatteryVoltageSlave4'] = "-1"
                                    device_properties['BatteryVoltageSlave5'] = "-1"
                                    device_properties['BatteryVoltageSlave6'] = "-1"
                                    device_properties['BatteryVoltageSlave7'] = "-1"
                                    device_properties['ChargeVoltageMain'] = "-1"
                                    device_properties['ChargeVoltageSlave1'] = "-1"
                                    device_properties['ChargeVoltageSlave2'] = "-1"
                                    device_properties['ChargeVoltageSlave3'] = "-1"
                                    device_properties['ChargeVoltageSlave4'] = "-1"
                                    device_properties['ChargeVoltageSlave5'] = "-1"
                                    device_properties['ChargeVoltageSlave6'] = "-1"
                                    device_properties['ChargeVoltageSlave7'] = "-1"
                                    device_properties['ChargerStatus'] = "N/A"
                                    device_properties['BatteryStatus'] = "N/A"

                                #logging.debug("device_properties: %s", device_properties)

                                self.UpdateDeviceInfo(True)     # Update Device properties.

                            elif line[1:3] == "EL":       # Determine HW model number CM9000/9001 if available and number of Slave confirmation.
                                ELMsg = Comfort_EL_HardwareModelReport(line[1:])
                                                 
                                device_properties['ComfortHardwareModel'] = str(ELMsg.hardwaremodel)

                                logging.debug("Hardware Model %s", str(device_properties['ComfortHardwareModel']))
                                self.UpdateDeviceInfo(True)     # Update Device properties. Issue with no CCLX file and ComfortFileSyste, = Null.

                            elif line[1:3] == "D?":       # Get Battery/Charge or DC Supply voltage. ARM/Toshiba + CM-9001 Only.

                                # Determine Battery/Charge Voltage and Device ID. Save Values in Comfort_D_SystemVoltageReport
                                DLMsg = Comfort_D_SystemVoltageReport(line[1:])     # Return value not used currently.
                                self.UpdateBatteryStatus()
                                #self.UpdateDeviceInfo(True)     # Update Device properties.
                                
                            elif line[1:5] == "SN01":       # Comfort Encoded Serial Number - Used for Refresh Key
                                SNMsg = ComfortSN_SerialNumberReport(line[1:])
                                if COMFORT_SERIAL != SNMsg.serial_number:
                                    pass
                                COMFORT_KEY = SNMsg.refreshkey
                                logging.info("Refresh Key: %s", COMFORT_KEY)
                                logging.info("Serial Number: %s", COMFORT_SERIAL)
                                device_properties['SerialNumber'] = COMFORT_SERIAL
                                
                                self.UpdateDeviceInfo(True)     # Update Device properties.

                            elif line[1:3] == "a?":     # Not Fully Implemented. For Future Development !!!
                                aMsg = Comfort_A_SecurityInformationReport(line[1:])
                                ALARMSTATE = aMsg.SS         # Save Numerical state.
                                self.publish(ALARMSTATUSTOPIC, aMsg.state, qos=2, retain=True)          
                                if aMsg.type == 'LowBattery':
                                    logging.warning("Low Battery - %s", aMsg.battery)
                                elif aMsg.type == 'PowerFail':
                                    logging.warning("AC Fail")      # Comfort doesn't yet report which unit fails.
                                elif aMsg.type == 'Disarm':
                                    logging.info("System Disarmed")

                            elif line[1:3] == "ER" and CacheState:           
                                erMsg = ComfortERArmReadyNotReady(line[1:])
                                if not erMsg.zone == 0:

                                    if ZONEMAPFILE & self.CheckIndexNumberFormat(str(erMsg.zone)):
                                        logging.warning("Zone %s (%s) Not Ready", str(erMsg.zone), input_properties[str(erMsg.zone)]['Name'])
                                        message_topic = "Zone "+str(erMsg.zone)+ " ("+str(input_properties[str(erMsg.zone)]['Name'])+ ") Not Ready"
                                    else: 
                                        logging.warning("Zone %s Not Ready", str(erMsg.zone))
                                        message_topic = "Zone "+str(erMsg.zone)+ " Not Ready"

                                    #message_topic = "Zone "+str(erMsg.zone)+ " Not Ready"
                                    self.publish(ALARMMESSAGETOPIC, message_topic, qos=2, retain=True)          # Empty string removes topic.
                                else:
                                    logging.info("Ready To Arm...")
                                    # Sending KD1A when receiving ER message confuses Comfort. When arming local to any mode it immediately goes into Arm Mode
                                    # Not all Zones are announced and it 'presses' the '#' key on your behalf.
                                    # self.comfortsock.sendall("\x03KD1A\r".encode()) #Force Arm, acknowledge Open Zones and Bypasses them.

                            elif line[1:3] == "AM":    # AM/AR for Non-Detector alarms
                                amMsg = ComfortAMSystemAlarmReport(line[1:])
                                logging.warning(amMsg.message)
                                #if amMsg.parameter <= int(COMFORT_INPUTS):
                                self.publish(ALARMMESSAGETOPIC, amMsg.message, qos=2, retain=True)
                                if amMsg.triggered:
                                    self.publish(ALARMSTATETOPIC, "triggered", qos=2, retain=False)     # Original message

                            #elif line[1:3] == "AL":     # Under development (Alarm Type Report)
                            #    alMsg = ComfortALSystemAlarmReport(line[1:])
                            #    match ALARMSTATE:
                            #        case 0:     # Idle
                            #            self.publish(ALARMSTATUSTOPIC, "Idle", qos=2, retain=False)
                            #        case 1:     # Trouble
                            #            self.publish(ALARMSTATUSTOPIC, "Trouble", qos=2, retain=False)
                            #        case 2:     # Alert
                            #            self.publish(ALARMSTATUSTOPIC, "Alert", qos=2, retain=False)
                            #        case 3:     # Alarm
                            #            self.publish(ALARMSTATUSTOPIC, "Alarm", qos=2, retain=False)
                            #        case _:     # Unknown (default)
                            #            self.publish(ALARMSTATUSTOPIC, "Unknown", qos=2, retain=False)

                                #if alMsg.parameter <= int(COMFORT_INPUTS):
                                #    self.publish(ALARMMESSAGETOPIC, alMsg.message, qos=2, retain=True)
                                #    logging.warning("Tamper %s", str(alMsg.parameter))
                                #    if alMsg.triggered:
                                #        self.publish(ALARMSTATETOPIC, "triggered", qos=2, retain=False)     # Original message
                            
                            elif line[1:3] == "AR":
                                arMsg = ComfortARSystemAlarmReport(line[1:])
                                self.publish(ALARMMESSAGETOPIC, arMsg.message,qos=2,retain=True)
                                #logging.info(arMsg.message)        # Removed logging for AR as it duplicates messages.

                            elif line[1:3] == "EX":
                                exMsg = ComfortEXEntryExitDelayStarted(line[1:])
                                self.entryexitdelay = exMsg.delay
                                self.entryexit_timer()
                                if exMsg.type == 1:         # Entry Delay
                                    self.publish(ALARMSTATETOPIC, "pending",qos=2,retain=False)
                                elif exMsg.type == 2:       # Exit Delay
                                    self.publish(ALARMSTATETOPIC, "arming",qos=2,retain=False)

                            elif line[1:3] == "RP":
                                if line[3:5] == "01":
                                    self.publish(ALARMMESSAGETOPIC, "Phone Ring",qos=2,retain=True)
                                elif line[3:5] == "00":
                                    self.publish(ALARMMESSAGETOPIC, "",qos=2,retain=True)   # Stopped Ringing
                                elif line[3:5] == "FF":
                                    self.publish(ALARMMESSAGETOPIC, "Phone Answer",qos=2,retain=True)

                            elif line[1:3] == "DB":
                                if line[3:5] == "FF":
                                    self.publish(ALARMMESSAGETOPIC, "",qos=2,retain=True)
                                    self.publish(ALARMDOORBELLTOPIC, 0,qos=2,retain=True)
                                else:
                                    self.publish(ALARMDOORBELLTOPIC, 1, qos=2,retain=True)
                                    self.publish(ALARMMESSAGETOPIC, "Door Bell",qos=2,retain=True)

                            elif line[1:3] == "OP" and CacheState:
                                ipMsg = ComfortOPOutputActivationReport(line[1:])

                                if ipMsg.state < 2:
                                    _time = datetime.now().replace(microsecond=0).isoformat()
                                    if ipMsg.output <= 128:
                                        try:
                                            _name = output_properties[str(ipMsg.output)] if OUTPUTMAPFILE else "Output" + "{:03d}".format(ipMsg.output)
                                        except KeyError as e:
                                            _name = "Output" + "{:03d}".format(ipMsg.output)
                                    else:
                                        try:
                                            _name = output_properties[str(ipMsg.output)] if OUTPUTMAPFILE else "ScsRioOutput" + str(ipMsg.output)
                                        except KeyError as e:
                                            _name = "ScsRioOutput" + str(ipMsg.output)
                                    MQTT_MSG=json.dumps({"Time": _time, 
                                                         "Name": _name, 
                                                         "State": ipMsg.state
                                                        })
                                    if ipMsg.output <= int(COMFORT_OUTPUTS) or ipMsg.output > 128:
                                        self.publish(ALARMOUTPUTTOPIC % ipMsg.output, MQTT_MSG,qos=2,retain=False)    # 19/8/2024 Changed to False
                                        time.sleep(0.01)

                            elif line[1:3] == "Y?":     # Comfort Outputs
                                yMsg = ComfortY_ReportAllOutputs(line[1:])
                                for opMsgY in yMsg.outputs:
                                    _time = datetime.now().replace(microsecond=0).isoformat()
                                    try:
                                        _name = output_properties[str(opMsgY.output)] if OUTPUTMAPFILE else "Output" + "{:03d}".format(opMsgY.output)
                                    except KeyError as e:
                                        if int(e.args[0]) < ALARMNUMBEROFOUTPUTS:
                                            logging.debug ("Output %s not in CCLX file, ignoring CCLX enrichment", str(e))
                                        _name = "Output" + "{:03d}".format(opMsgY.output)
                                    MQTT_MSG=json.dumps({"Time": _time, 
                                                         "Name": _name,
                                                         "State": opMsgY.state
                                                        })
                                    if opMsgY.output <= int(COMFORT_OUTPUTS):
                                        self.publish(ALARMOUTPUTTOPIC % opMsgY.output, MQTT_MSG,qos=2,retain=False)
                                    else:
                                        self.publish(ALARMOUTPUTTOPIC % opMsgY.output, "",qos=2,retain=False)     # Remove any previously created objects
                                    time.sleep(0.01)    # 10mS delay between commands
                                logger.debug("Max. Reported Outputs: %d", yMsg.max_zones)
                                if yMsg.max_zones < int(COMFORT_OUTPUTS):
                                    logger.warning("Max. Reported Outputs of %d is less than the configured value of %s", yMsg.max_zones, COMFORT_OUTPUTS)

                            elif line[1:3] == "y?":     # SCS/RIO Outputs
                                yMsg = Comfort_Y_ReportAllOutputs(line[1:])
                                for opMsgY in yMsg.outputs:
                                    _time = datetime.now().replace(microsecond=0).isoformat()
                                    try:
                                        _name = output_properties[str(opMsgY.output)] if OUTPUTMAPFILE else "ScsRioOutput" + str(opMsgY.output)
                                    except KeyError as e:
                                        if int(COMFORT_RIO_OUTPUTS) > 0 and int(e.args[0]) < ALARMRIOOUTPUTRANGE[-1]:
                                            logging.debug ("SCS/RIO Output %s not in CCLX file, ignoring CCLX enrichment", str(e))
                                        _name = "ScsRioOutput" + str(opMsgY.output)
                                    MQTT_MSG=json.dumps({"Time": _time, 
                                                         "Name": _name, 
                                                         "State": opMsgY.state
                                                        })
                                    if opMsgY.output <= 128 + int(COMFORT_RIO_OUTPUTS):
                                        self.publish(ALARMOUTPUTTOPIC % opMsgY.output, MQTT_MSG,qos=2,retain=False)
                                    else:
                                        self.publish(ALARMOUTPUTTOPIC % opMsgY.output, "",qos=2,retain=False)     # Remove any previously created objects
                                    time.sleep(0.01)    # 10mS delay between commands 

                                logger.debug("Max. Reported SCS/RIO Outputs: %d", yMsg.max_zones)

                            elif line[1:5] == "r?00":
                                cMsg = Comfort_R_ReportAllSensors(line[1:])
                                for cMsgr in cMsg.counters:
                                    _time = datetime.now().replace(microsecond=0).isoformat()
                                    try:
                                        _name = counter_properties[str(cMsgr.counter)] if COUNTERMAPFILE else "counter" + str(cMsgr.counter)
                                    except KeyError as e:
                                        _name = "counter" + str(cMsgr.counter)
                                    MQTT_MSG=json.dumps({"Time": _time, 
                                                         "Name": _name,
                                                         "Value": cMsgr.value,
                                                         "State": cMsgr.state
                                                        })
                                    self.publish(ALARMCOUNTERINPUTRANGE % cMsgr.counter, MQTT_MSG,qos=2,retain=False)
                                    time.sleep(0.01)    # 10mS delay between commands

                            elif line[1:5] == "r?01":
                                sMsg = Comfort_R_ReportAllSensors(line[1:])
                                for sMsgr in sMsg.sensors:
                                    _time = datetime.now().replace(microsecond=0).isoformat()
                                    try:
                                        _name = sensor_properties[str(sMsgr.sensor)] if SENSORMAPFILE else "sensor" + str(sMsgr.sensor)
                                    except KeyError as e:
                                        logging.debug ("Sensor %s not in CCLX file, ignoring CCLX enrichment", str(e))
                                        _name = "sensor" + str(sMsgr.sensor)
                                    MQTT_MSG=json.dumps({"Time": _time, 
                                                         "Name": _name,
                                                         "Value": sMsgr.value
                                                        })
                                    self.publish(ALARMSENSORTOPIC % sMsgr.sensor, MQTT_MSG,qos=2,retain=False)
                                    time.sleep(0.01)    # 10mS delay between commands

                            elif (line[1:3] == "f?") and (len(line) == 69):
                                fMsg = Comfortf_ReportAllFlags(line[1:])
                                for fMsgf in fMsg.flags:
                                    _time = datetime.now().replace(microsecond=0).isoformat()
                                    try:
                                        _name = flag_properties[str(fMsgf.flag)] if FLAGMAPFILE else "flag" + str(fMsgf.flag)
                                    except KeyError as e:
                                        logging.debug ("Flag %s not in CCLX file, ignoring CCLX enrichment", str(e))
                                        _name = "flag" + str(fMsgf.flag)
                                    MQTT_MSG=json.dumps({"Time": _time, 
                                                         "Name": _name,
                                                         "State": fMsgf.state
                                                        })
                                    self.publish(ALARMFLAGTOPIC % fMsgf.flag, MQTT_MSG,qos=2,retain=False)
                                    time.sleep(0.01)    # 10mS delay between commands

                            elif (line[1:3] == "b?"):   # and (len(line) == 69):
                                bMsg = ComfortB_ReportAllBypassZones(line[1:])
                                if bMsg.value == 0:
                                    logger.debug("Zones Bypassed: <None>")
                                    self.publish(ALARMBYPASSTOPIC, 0, qos=2, retain=True)
                                else:
                                    logger.debug("Zones Bypassed: %s", bMsg.value)
                                    self.publish(ALARMBYPASSTOPIC, bMsg.value, qos=2,retain=True)

                            elif (line[1:9] == "DL7FF904"):
                                if len(line[1:]) == 18:
                                    device_properties['uid'] = line[9:17]
                                    DECODED_SERIAL = ComfortSN_SerialNumberReport(line[5:17])      # Decode raw data to get SN. SN command not working for some versions of firmware.
                                    if DECODED_SERIAL.serial_number != COMFORT_SERIAL:             # Check if SN and DL data match. 
                                        COMFORT_SERIAL = DECODED_SERIAL.serial_number
                                        device_properties['SerialNumber'] = COMFORT_SERIAL
                                else:
                                    device_properties['uid'] = "00000000"

                            elif line[1:3] == "FL" and CacheState:
                                flMsg = ComfortFLFlagActivationReport(line[1:])
                                try:
                                    _name = flag_properties[str(flMsg.flag)] if FLAGMAPFILE else "Flag" + "{:03d}".format(flMsg.flag)
                                except KeyError as e:
                                    _name = "Flag" + "{:03d}".format(flMsg.flag)
                                MQTT_MSG=json.dumps({"Time": _time, 
                                                     "Name": _name,
                                                     "State": flMsg.state
                                                    })
                                self.publish(ALARMFLAGTOPIC % flMsg.flag, MQTT_MSG,qos=2,retain=False)
                                time.sleep(0.01)    # 10mS delay between commands

                            elif line[1:3] == "BY" and CacheState:
                                byMsg = ComfortBYBypassActivationReport(line[1:])   
                                _time = datetime.now().replace(microsecond=0).isoformat()

                                if byMsg.zone <= int(COMFORT_INPUTS):        # Was 128, changed to configured Zones.
                                    try:
                                        _name = input_properties[str(byMsg.zone)]['Name'] if ZONEMAPFILE else "Zone" + str(byMsg.zone)
                                    except KeyError as e:
                                        _name = "Zone" + str(byMsg.zone)
                                    try:
                                        _zoneword = input_properties[str(byMsg.zone)]['ZoneWord'] if ZONEMAPFILE else ""
                                    except KeyError as e:
                                        _zoneword = ""
                                else:
                                    pass

                                _state = ZoneCache[byMsg.zone]
                                BypassCache[byMsg.zone] = byMsg.state if byMsg.zone <= int(COMFORT_INPUTS) else None

                                if byMsg.state == 1 and byMsg.zone <= int(COMFORT_INPUTS):
                                    if ZONEMAPFILE and self.CheckIndexNumberFormat(str(byMsg.zone)):
                                        logging.warning("Zone %s (%s) Bypassed", str(byMsg.zone), _name)
                                    else: logging.warning("Zone %s Bypassed", str(byMsg.zone))
                                elif byMsg.state == 0 and byMsg.zone <= int(COMFORT_INPUTS):
                                    if ZONEMAPFILE and self.CheckIndexNumberFormat(str(byMsg.zone)):
                                        logging.info("Zone %s (%s) Unbypassed", str(byMsg.zone), _name)
                                    else: logging.info("Zone %s Unbypassed", str(byMsg.zone))

                                MQTT_MSG=json.dumps({"Time": _time, 
                                                     "Name": _name,
                                                     "ZoneWord": _zoneword if byMsg.zone <= int(COMFORT_INPUTS) else None,
                                                     "State": _state, 
                                                     "Bypass": BypassCache[byMsg.zone] if byMsg.zone <= int(COMFORT_INPUTS) else None
                                                    })
                                if byMsg.zone <= int(COMFORT_INPUTS):
                                    self.publish(ALARMINPUTTOPIC % byMsg.zone, MQTT_MSG,qos=2,retain=False)    # 19/8/2024 Changed to False
                                    time.sleep(0.01)    # 10mS delay between commands

                                    self.publish(ALARMBYPASSTOPIC, byMsg.value, qos=2,retain=True)  # Add Zone to list of zones.
                                    time.sleep(0.01)    # 10mS delay between commands

                            elif line[1:3] == "RS":
                                #on rare occassions comfort ucm might get reset (RS11), our session is no longer valid, need to relogin
                                logger.warning('Reset detected')
                                self.login()
                            else:
                                if datetime.now() > (SAVEDTIME + TIMEOUT):  # If no command sent in 30 seconds then send keepalive.
                                    self.comfortsock.sendall("\x03cc00\r".encode()) #echo command for keepalive. cc00
                                    SAVEDTIME = datetime.now()
                                    time.sleep(0.1)
                        else:
                            logger.warning("Invalid response received (%s)", line.encode())

                #except socket.error as v:
                except (socket.error, ConnectionResetError, BrokenPipeError, TimeoutError) as v:
                    logger.error('Comfort Socket Error %s', str(v))
                finally:        # Added 29/4/2025
                    if self.comfortsock:
                        try:
                            self.comfortsock.close()
                        except Exception:
                            pass
                        self.comfortsock = None


                COMFORTCONNECTED = False
                FIRST_LOGIN = True  # Added 29/4/2025
                logger.error('Lost connection to Comfort, reconnecting...')
                if BROKERCONNECTED == True:      # MQTT Connected ??
                    self.publish(ALARMAVAILABLETOPIC, 0,qos=2,retain=True)
                    self.publish(ALARMLWTTOPIC, 'Offline',qos=2,retain=True)
                    self.publish(ALARMCONNECTEDTOPIC, "1" if COMFORTCONNECTED else "0", qos=2, retain=False)
                    
                time.sleep(RETRY.seconds)
        except KeyboardInterrupt as e:
            logger.debug("SIGINT (Ctrl-C) Intercepted")
            logger.info('Shutting down.')
            self.exit_gracefully(1,1)
            if self.connected == True:
                device_properties['BridgeConnected'] = 0
                try:
                    self.comfortsock.sendall("\x03LI\r".encode()) #Logout command.
                except:
                    pass
            RUN = False
            self.loop_stop
        finally:
            if BROKERCONNECTED == True:      # MQTT Connected ??
                infot = self.publish(ALARMAVAILABLETOPIC, 0,qos=2,retain=True)
                infot = self.publish(ALARMLWTTOPIC, 'Offline',qos=2,retain=True)
                infot.wait_for_publish(1)
                self.loop_stop


def validate_certificate(certificate):
    # Check Valid Certificate file and Valid Dates. NotBefore and NotAfter must be within datetime.now()

    if not os.path.isfile(certificate):
        return 2    # Missing certificate
    # Open the certificate file in binary mode
    with open(certificate, 'rb') as cert_file:
        cert_data = cert_file.read()

    try:
        # Load the certificate using the binary data
        x509 = crypto.load_certificate(crypto.FILETYPE_PEM, cert_data)

        # Check the 'notAfter' attribute
        not_after = x509.get_notAfter()
        not_before = x509.get_notBefore() 
        if not_after:
            ValidTo = not_after.decode()
        if not_before:
            ValidFrom = not_before.decode()

        # Define the format of the datetime strings
        datetime_format = "%Y%m%d%H%M%SZ"

        # Convert the strings to datetime objects
        ValidTo = datetime.strptime(ValidTo, datetime_format)
        ValidFrom = datetime.strptime(ValidFrom, datetime_format)
    
        if (datetime.now() >= ValidFrom) and (datetime.now() < ValidTo):
            return 0    # Valid certificate
        else:
            return 1    # Expired certificate
    except crypto.Error as e:
        raise ValueError(f"Error loading certificate: {e}")

mqttc = Comfort2(callback_api_version = mqtt.CallbackAPIVersion.VERSION2, client_id=mqtt_client_id, protocol=mqtt.MQTTv5, transport=MQTT_PROTOCOL)

certs: str = "/config/certificates"                 # Certificates directory directly off the root.
if MQTT_ENCRYPTION and not os.path.isdir(certs):    # Display warning if Encryption is enabled but certificates directory is not found.
    logging.debug('"/config/certificates" directory not found.')

if((MQTT_CA_CERT and MQTT_CA_CERT.strip())): ca_cert = os.sep.join([certs, MQTT_CA_CERT])
if((MQTT_CLIENT_CERT and MQTT_CLIENT_CERT.strip())): client_cert = os.sep.join([certs, MQTT_CLIENT_CERT])
if((MQTT_CLIENT_KEY and MQTT_CLIENT_KEY.strip())): client_key = os.sep.join([certs, MQTT_CLIENT_KEY])

if not MQTT_ENCRYPTION:
    logging.warning('MQTT Transport Layer Security disabled.')
else:
    ### Check some certificate validity here ###
    match  validate_certificate(ca_cert):
        case 1:     # Invalid CA Certificate
            logging.warning('MQTT TLS CA Certificate Expired or not Valid (%s)', ca_cert )
            logging.warning("Reverting MQTT Port to default '1883' (Unencrypted)")
            MQTTBROKERPORT = 1883
            MQTT_ENCRYPTION = False

        case 2:     # Certificate not found
            logging.warning('No MQTT TLS CA Certificate found, disabling TLS')
            logging.warning("Reverting MQTT Port to default '1883'")
            MQTTBROKERPORT = 1883
            MQTT_ENCRYPTION = False

        case 3:     # Invalid Client Certificate or Key
            logging.warning('Client Key or Certificate Expired or Invalid')

        case 0:     # Valid Certificate
            logging.debug('Valid MQTT TLS CA Certificate found (%s)', ca_cert )
            tls_args = {}
            tls_args['ca_certs'] = ca_cert
            mqttc.tls_set(**tls_args, tls_version=ssl.PROTOCOL_TLSv1_2)
            #mqttc.tls_insecure_set(True)
            mqttc.tls_insecure_set(False)

        case _:
            # Default
            pass

mqttc.init(MQTTBROKERIP, MQTTBROKERPORT, MQTTUSERNAME, MQTTPASSWORD, COMFORTIP, COMFORTPORT, PINCODE, mqtt.MQTTv5)
mqttc.run()
