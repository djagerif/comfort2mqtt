# Copyright(c) 2018 Khor Chin Heong (koochyrat@gmail.com) for original project code and additional 
# Copyright(c) 2024 Ingo de Jager (ingodejager@gmail.com) for modifications done 
# to the original project sources contained in this project.
#
# Modified by Ingo de Jager 2024 (ingodejager@gmail.com)
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
### Future Encryption option ###
### Option: `MQTT Transport Encryption` (Optional) - Not currently used
###
### The MQTT traffic can be encrypted with `TLS` or sent in clear-text. The Encryption option is currently not available. The default is `False`
#
import csv
import os
from pathlib import Path
import re
import signal
import socket
import time
import datetime
import threading
import logging
from datetime import datetime, timedelta
#from random import randint
import paho.mqtt.client as mqtt
from argparse import ArgumentParser

DOMAIN = "comfort2"

#rand_hex_str = hex(randint(268435456, 4294967295))
#mqtt_client_id = DOMAIN+"-"+str(rand_hex_str[2:])       # Generate random client-id each time it starts, for future development of a possible second instance.
mqtt_client_id = DOMAIN+"mqtt"

ALARMSTATETOPIC = DOMAIN+"/alarm"
ALARMSTATUSTOPIC = DOMAIN+"/alarm/status"
ALARMBYPASSTOPIC = DOMAIN+"/alarm/bypass"               # List of Bypassed Zones.

ALARMCOMMANDTOPIC = DOMAIN+"/alarm/set"
ALARMAVAILABLETOPIC = DOMAIN+"/alarm/online"
ALARMLWTTOPIC = DOMAIN+"/alarm/LWT"
ALARMMESSAGETOPIC = DOMAIN+"/alarm/message"
#ALARMEXTMESSAGETOPIC = DOMAIN+"/alarm/ext_message"     # Extended Messages will be available here.  For future development !!!
ALARMTIMERTOPIC = DOMAIN+"/alarm/timer"
ALARMDOORBELLTOPIC = DOMAIN+"/doorbell"

FIRST_LOGIN = False         # Don't scan Comfort until MQTT connection is made.
RUN = True
#SAVEDTIME = datetime.now()  # Used for sending keepalives to Comfort.
BYPASSEDZONES = []          # Global list of Bypassed Zones
BROKERCONNECTED = False
ZONEMAPFILE = False         # Zone Number to Name CSV file present.

logger = logging.getLogger(__name__)

def boolean_string(s):
    if s not in {'false', 'true'}:
        raise ValueError('Not a valid boolean string')
    return s == 'true'

parser = ArgumentParser()

group = parser.add_argument_group('MQTT options')
group.add_argument(
    '--broker-address',
    required=True,
    help='Address of the MQTT broker')

group.add_argument(
    '--broker-port',
    type=int, default=1883,
    help='Port to use to connect to the MQTT broker. [default: 1883]')

group.add_argument(
    '--broker-username',
    required=True,
    help='Username to use for MQTT broker authentication.')

group.add_argument(
    '--broker-password',
    required=True,
    help='Password to use for MQTT broker authentication.')

group.add_argument(
    '--broker-protocol',
    required=False,
    dest='broker_protocol', default='TCP', choices=(
         'TCP', 'WebSockets'),
    help='TCP or WebSockets Transport Protocol for MQTT broker. [default: TCP]')

#  For future development !!!
#group.add_argument(
#    '--broker-encryption',
#    required=False,
#    type=boolean_string, default='false',
#    help='Use TLS encryption. [default: False]')

group = parser.add_argument_group('Comfort System options')
group.add_argument(
    '--comfort-address',
    required=True,
    help='Address of the Comfort system')

group.add_argument(
    '--comfort-port',
    type=int, default=1002,
    help='Port to use to connect to the Comfort system. [default: 1002]')

group.add_argument(
    '--comfort-login-id',
    required=True,
    help='Comfort system Login ID.')

group.add_argument(
    '--comfort-time',
    type=boolean_string, default='false',
    help='Set Comfort II Date and Time flag. [default: False]')

group = parser.add_argument_group('Comfort Alarm options')
group.add_argument(
    '--alarm-inputs',
    type=int, default=8,
    help='Number of physical Zone Inputs')

group.add_argument(
    '--alarm-outputs',
    type=int, default=0,
    help='Number of physical Zone Outputs')

group.add_argument(
    '--alarm-responses',
    type=int, default=0,
    help='Number of Responses')

group.add_argument(
    '--alarm-rio-inputs',
    type=int, default=0,
    help='Number of SCS/RIO Inputs')

group.add_argument(
    '--alarm-rio-outputs',
    type=int, default=0,
    help='Number of SCS/RIO Outputs')

group = parser.add_argument_group('Logging options')
group.add_argument(
    '--verbosity',
    dest='verbosity', default='INFO', choices=(
        'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'),
    help='Verbosity of logging to emit [default: %(default)s]')

option = parser.parse_args()

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=option.verbosity,
    datefmt='%Y-%m-%d %H:%M:%S'
)

### Testing Area ###
TOKEN = os.getenv('SUPERVISOR_TOKEN')
#
uri = "ws://supervisor/core/websocket"
#
auth_message = json.dumps({
    "type": "auth",
    "access_token": TOKEN
})

headers = {
    "Authorization": "Bearer {}".format(TOKEN),
    "content-type": "application/json",
}

### End Testing Area ###

logger.info('Importing the add-on configuration options')

MQTT_USER=option.broker_username
MQTT_PASSWORD=option.broker_password
MQTT_SERVER=option.broker_address
MQTT_PORT=option.broker_port
MQTT_PROTOCOL=option.broker_protocol
#MQTT_ENCRYPTION=option.broker_encryption               #  For future development !!!
COMFORT_ADDRESS=option.comfort_address
COMFORT_PORT=option.comfort_port
COMFORT_LOGIN_ID=option.comfort_login_id
MQTT_LOG_LEVEL=option.verbosity
COMFORT_INPUTS=int(option.alarm_inputs)
COMFORT_OUTPUTS=int(option.alarm_outputs)
COMFORT_RESPONSES=int(option.alarm_responses)
COMFORT_TIME=str(option.comfort_time)
COMFORT_RIO_INPUTS=str(option.alarm_rio_inputs)
COMFORT_RIO_OUTPUTS=str(option.alarm_rio_outputs)

ALARMINPUTTOPIC = DOMAIN+"/input%d"                     #input1,input2,... input128 for every input. Physical Inputs (Default 8), Max 128
ALARMINPUTBYPASSTOPIC = DOMAIN+"/input%d/bypass"        # Bypass Status.
if int(COMFORT_INPUTS) < 8:
    COMFORT_INPUTS = "8"
ALARMVIRTUALINPUTRANGE = range(1,int(COMFORT_INPUTS)+1) #set this according to your system. Starts at 1 -> {value}
ALARMINPUTCOMMANDTOPIC = DOMAIN+"/input%d/set"          #input1,input2,... input128 for virtual inputs

ALARMRIOINPUTTOPIC = DOMAIN+"/input%d"                  #input129,input130,... input248 for every input. Physical SCS/RIO Inputs (Default 0), Max 120  
if int(COMFORT_RIO_INPUTS) < 0:
    COMFORT_RIO_INPUTS = "0"
ALARMRIOINPUTRANGE = range(129,129+int(COMFORT_RIO_INPUTS))   #set this according to your system. Starts at 129 -> 248 (Max.)
ALARMRIOINPUTCOMMANDTOPIC = DOMAIN+"/input%d/set"       #input129,input130,... input248 for SCS/RIO inputs. Cannot set as Virtual Input.

ALARMOUTPUTTOPIC = DOMAIN+"/output%d"                   #output1,output2,... for every output
if int(COMFORT_OUTPUTS) < 0:
    COMFORT_OUTPUTS = "0"
ALARMNUMBEROFOUTPUTS = int(COMFORT_OUTPUTS)             #set this according to your system. Physical Outputs (Default 0), Max 96
ALARMOUTPUTCOMMANDTOPIC = DOMAIN+"/output%d/set"        #output1/set,output2/set,... for every output

ALARMRIOOUTPUTTOPIC = DOMAIN+"/output%d"                #output129,output130,... for every SCS/RIO output
if int(COMFORT_RIO_OUTPUTS) < 0:
    COMFORT_RIO_OUTPUTS = "0"
ALARMRIOOUTPUTRANGE = range(129,129+int(COMFORT_RIO_OUTPUTS))    #set this according to your system. Physical SCS/RIO Outputs (Default 0), Max 120
ALARMRIOOUTPUTCOMMANDTOPIC = DOMAIN+"/output%d/set"     #output129,output130,... output248 for SCS/RIO outputs.

ALARMNUMBEROFRESPONSES = COMFORT_RESPONSES              #set this according to your system. Default 0, Max 1024
ALARMRESPONSECOMMANDTOPIC = DOMAIN+"/response%d/set"    #response1,response2,... for every response

ALARMNUMBEROFFLAGS = 254                                # Max Flags for system
ALARMFLAGTOPIC = DOMAIN+"/flag%d"                       #flag1,flag2,...flag254
ALARMFLAGCOMMANDTOPIC = DOMAIN+"/flag%d/set"            #flag1/set,flag2/set,... flag254/set

ALARMNUMBEROFSENSORS = 32                               # Use system default = 32 (0-31)
ALARMSENSORTOPIC = DOMAIN+"/sensor%d"                   #sensor0,sensor1,...sensor31
ALARMSENSORCOMMANDTOPIC = DOMAIN+"/sensor%d/set"        #sensor0,sensor1,...sensor31

ALARMNUMBEROFCOUNTERS = 255                             # Hardcoded to 255
ALARMCOUNTERINPUTRANGE = DOMAIN+"/counter%d"            #each counter represents a value EG. light level
ALARMCOUNTERCOMMANDTOPIC = DOMAIN+"/counter%d/set"      # set the counter to a value for between 0 (off) to 255 (full on) or any 16-bit value.
ALARMCOUNTERSTATETOPIC = DOMAIN+"/counter%d/state"      # Holds the state of the object, either ON or OFF depending on the value. # State On=1 or Off=0

ALARMTIMERREPORTTOPIC = DOMAIN+"/timer%d"               #each timer instance.
ALARMNUMBEROFTIMERS = 64                                # default timer instances. 1 - 64.

logger.info('Completed importing addon configuration options')

# The following variables values were passed through via the Home Assistant add on configuration options
logger.debug('The following variable values were passed through via the Home Assistant')
logger.debug('MQTT_USER = %s', MQTT_USER)
logger.debug('MQTT_PASSWORD = ******')
logger.debug('MQTT_SERVER = %s', MQTT_SERVER)
logger.debug('MQTT_PORT = %s', MQTT_PORT)             
logger.debug('MQTT_PROTOCOL = %s/%s', MQTT_PROTOCOL, MQTT_PORT)
#logger.debug('MQTT_ENCRYPTION = %s', MQTT_ENCRYPTION)  #  For future development !!!
logger.debug('COMFORT_ADDRESS = %s', COMFORT_ADDRESS)
logger.debug('COMFORT_PORT = %s', COMFORT_PORT)
logger.debug('COMFORT_LOGIN_ID = ******')
#logger.debug('MQTT_CA_CERT_PATH = %s', MQTT_CA_CERT_PATH)          #  For future development !!!
#logger.debug('MQTT_CLIENT_CERT_PATH = %s', MQTT_CLIENT_CERT_PATH)  #  For future development !!!
#logger.debug('MQTT_CLIENT_KEY_PATH = %s', MQTT_CLIENT_KEY_PATH)    #  For future development !!!

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
        #logger.debug("input: %d, state: %d", self.input, self.state)


class ComfortCTCounterActivationReport(object): # in format CT1EFF00 ie CT (counter) 1E = 30; state FF00 = 65280
    def __init__(self, datastr="", counter=0, value=0, state=0):
        #logger.debug("ComfortCTCounterActivationReport[datastr]: %s, [counter]: %s, [state]: %s", datastr, counter, state)
        if datastr:
            self.counter = int(datastr[2:4], 16)    #Integer value 3
            #logger.debug("ComfortCTCounterActivationReport[counter(int)]: %s", self.counter)
            self.value = self.ComfortSigned16(int("%s%s" % (datastr[6:8], datastr[4:6]),16))            # Use new 16-bit format
            self.state = self.state = 1 if (int(datastr[4:6],16) > 0) else 0                            # 8-bit value used for state
            #logger.debug("ComfortCTCounterActivationReport[state(int)]: %s", self.state)
        else:
            self.counter = counter
            self.value = value
            self.state = state

    def ComfortSigned16(self,value):                                            # Returns signed 16-bit value where required.
        return -(value & 0x8000) | (value & 0x7fff)
    
    ### Byte-Swap code below ###
    def HexToSigned16Decimal(self,value):                                       # Returns Signed Decimal value from HEX string EG. FFFF = -1
        #logger.debug("#321 HexToSigned16Decimal[value]: %s", value)
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
        #logger.debug("DataString: %s", datastr)
        #logger.debug("Flag: %s", flag)
        #logger.debug("Flag State: %s", state)

        if datastr:
            self.flag = int(datastr[2:4], 16)
            self.state = int(datastr[4:6], 16)
        else:
            self.flag = int(flag)
            self.state = int(state)

class ComfortBYBypassActivationReport(object):

    global BYPASSEDZONES

    def __init__(self, datastr="", zone=0, state=0):
        if datastr:
            self.zone = int(datastr[2:4],16)
            self.state = int(datastr[4:6],16)
        else:
            self.zone = int(zone,16)
            self.state = int(state,16)

        if (self.state == 0):
            if (self.zone in BYPASSEDZONES):
                BYPASSEDZONES.remove(self.zone)
                if BYPASSEDZONES.count(-1) == 0 and len(BYPASSEDZONES) == 0:
                    BYPASSEDZONES.append(-1)        # Add '-1' when last entry is removed.
            else:
                logger.debug("ValueError Exception: Bypassed Zone does not appear in BYPASSEDZONES List[]")
        elif (self.state == 1):                     # State == 1 meaning must be in bypasszones
            if (self.zone not in BYPASSEDZONES):
                BYPASSEDZONES.append(self.zone)
            if BYPASSEDZONES.count(-1) >= 1:        #Remove -1 that indicates empty list.
                BYPASSEDZONES.remove(-1)

        BYPASSEDZONES.sort(reverse=False)
        result_string = ','.join(map(str, BYPASSEDZONES))
        self.value = result_string

class ComfortZ_ReportAllZones(object):
    def __init__(self, data={}):
        self.inputs = []
        b = (len(data) - 2) // 2            #variable number of zones reported
        #logger.debug("data: %s", data)
        self.max_zones = b * 8
        for i in range(1,b+1):
            inputbits = int(data[2*i:2*i+2],16)
            for j in range(0,8):
                self.inputs.append(ComfortIPInputActivationReport("", 8*(i-1)+1+j,(inputbits>>j) & 1))

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
        #logger.debug("ReportAllSensors(data): %s", data)
        self.sensors = []
        self.counters = []
        b = (len(data) - 8) // 4             #Fixed number of sensors reported from r?01 command. 0-15 and 16-31.
        self.RegisterStart = int(data[4:6],16)
        self.RegisterType = int(data[2:4],16)
        #logger.debug("len(data) - 8 // 4: %s", b)
        #logger.debug("RegisterStart: %s", self.RegisterStart)
        #logger.debug("RegisterType: %s", self.RegisterType)
        for i in range(0,b):
            if self.RegisterType == 1:  #Sensor
                sensorbits = data[8+(4*i):8+(4*i)+4]
                
                #Swap bits here.
                #Change to Signed value here.
                self.value = int((sensorbits[2:4] + sensorbits[0:2]),16)
                self.sensor =  self.RegisterStart+i
                #logger.debug("Type:%d, Sensor:%s, Integer Value:%s" % (self.RegisterType, self.sensor, self.value))
                self.sensors.append(Comfort_RSensorActivationReport("", self.RegisterStart+i, self.value))
            else:   # Should be '0' or Counter
                counterbits = data[8+(4*i):8+(4*i)+4]   #0000
                #logger.debug("counterbits: %s", counterbits)
                self.value = int((counterbits[2:4] + counterbits[0:2]),16)
                self.state = 1 if (int(counterbits[0:2],16) > 0) else 0
                #logger.debug("value: %s", self.value)
                #logger.debug("state: %s", self.state)
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

    global BYPASSEDZONES
        
    def __init__(self, data={}):
        BYPASSEDZONES.clear()      #Clear contents and rebuild again.
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
                    if zone_state == 1:
                        BYPASSEDZONES.append(zone_number)
                        self.zones.append(ComfortBYBypassActivationReport("", hex(zone_number), hex(zone_state)))

        if len(BYPASSEDZONES) == 0:      # If No Zones Bypassed, enter '-1' in the List[]
            BYPASSEDZONES.append(-1)

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

#The current alarm state can be found by sending the S? query
#PC: S?
#UCM: S?nn
#nn 00 = Idle, 1 = Trouble, 2 = Alert, 3 = Alarm
class ComfortS_SecurityModeReport(object):
    def __init__(self, data={}):
        self.mode = int(data[2:4],16)
        if self.mode == 0: self.modename = "Idle"
        elif self.mode == 1: self.modename = "Trouble"
        elif self.mode == 2: self.modename = "Alert"
        elif self.mode == 3: self.modename = "Alarm"

#zone = 00 means system can be armed, no open zones
class ComfortERArmReadyNotReady(object):
    def __init__(self, data={}):
        self.zone = int(data[2:4],16)

class ComfortAMSystemAlarmReport(object):
    def __init__(self, data={}):
        self.alarm = int(data[2:4],16)
        self.triggered = True               # For Comfort Alarm State Alert, Trouble, Alarm
        self.parameter = int(data[4:6],16)
        low_battery = ['','Slave 1','Slave 2','Slave 3','Slave 4','Slave 5','Slave 6','Slave 7']
        if self.alarm == 0: self.message = "Intruder, Zone "+str(self.parameter)
        elif self.alarm == 1: self.message = "Zone "+str(self.parameter)+" Trouble"
        elif self.alarm == 2: self.message = "Low Battery - "+('Main' if self.parameter == 1 else low_battery[(self.parameter - 32)])
        elif self.alarm == 3: self.message = "Power Failure - "+('Main' if self.parameter == 1 else low_battery[(self.parameter - 32)])
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
        elif self.alarm == 23: self.message = "New Message, User"+str(self.parameter); self.triggered = False
        elif self.alarm == 24: self.message = "Doorbell "+str(self.parameter); self.triggered = False
        elif self.alarm == 25: self.message = "Comms Failure RS485 id"+str(self.parameter)
        elif self.alarm == 26: self.message = "Signin Tamper "+str(self.parameter)
        else: self.message = "Unknown("+str(self.alarm)+")"

#a? - Current Alarm Information Request/Reply
#UCM a?AASS[XXYYBBzzRRTTGG]
#XX is Trouble bits
#Bit 0 = AC Failure
#Bit 1 = Low Battery
#Bit 2 = Zone Trouble
#Bit 3 = RS485 Comms Fail
#Bit 4 = Tamper
#Bit 5 = Phone Trouble
#Bit 6 = GSM trouble
#Bit 7 = Unused

class Comfort_A_SecurityInformationReport(object):      #  For future development !!!
    #a?000000000000000000
    def __init__(self, data={}):
        self.AA = int(data[2:4],16)     #AA is the current Alarm Type 01 to 1FH (Defaults can be changed in Comfigurator)
        self.SS = int(data[4:6],16)     #SS is alarm state 0-3 (Idle, Trouble, Alert, Alarm)
        self.XX = int(data[6:8],16)     #XX is Trouble bits
        self.YY = int(data[8:10],16)    #YY is for Spare Trouble Bits, 0 if unused
        self.BB = int(data[10:12],16)   #BB = Low Battery ID = 0 for Comfort or none
        self.zz = int(data[12:14],16)   #zz = Zone Trouble number, =0 if none
        self.RR = int(data[14:16],16)   #RR = RS485 Trouble ID, = 0 if none
        self.TT = int(data[16:18],16)   #TT = Tamper ID = 0 if none
        self.GG = int(data[18:20],16)   #GG = GSM ID =0 if no trouble
        #self.triggered = True   #for comfort alarm state Alert, Trouble, Alarm
        #logger.debug('a? - data: %s  - still under development', str(data[2:]))
        alarm_type = ['','Intruder','Duress','LineCut','ArmFail','ZoneTrouble','ZoneAlert','LowBattery', 'PowerFail', 'Panic', 'EntryAlert', \
                      'Tamper','Fire','Gas','FamilyCare','Perimeter', 'BypassZone','Disarm','CMSTest','SystemArmed', 'AlarmAbort', 'EntryWarning', \
                      'SirenTrouble','AlarmType23', 'RS485Comms','Doorbell','HomeSafe','DialTest','AlarmType28','NewMessage','Temperature','SigninTamper']
        alarm_state = ['Idle','Trouble','Alert','Alarm']
        low_battery = ['Main','Slave 1','Slave 2','Slave 3','Slave 4','Slave 5','Slave 6','Slave 7']
        self.type = alarm_type[self.AA]
        self.state = alarm_state[self.SS]
        if alarm_type == "LowBattery" and self.BB == 0: self.battery = low_battery[0]
        elif alarm_type == "LowBattery" and self.BB > 0:self.battery = low_battery[(self.BB - 32)]
        #logger.debug('Battery ID: %s', self.id)
        #logger.debug('Alarm Type: %s', self.type)       # What happens if you have low battery and zone trouble ????


class ComfortARSystemAlarmReport(object):
    def __init__(self, data={}):
        self.alarm = int(data[2:4],16)
        self.triggered = True   #for comfort alarm state Alert, Trouble, Alarm
        self.parameter = int(data[4:6],16)
        low_battery = ['','Slave 1','Slave 2','Slave 3','Slave 4','Slave 5','Slave 6','Slave 7']
        #logger.debug('AR - data: %s', str(data))
        if self.alarm == 1: self.message = "Zone "+str(self.parameter)+" Trouble"+" Restore"
        elif self.alarm == 2: self.message = "Low Battery - "+('Main' if self.parameter == 1 else low_battery[(self.parameter - 32)])+" Restore"
        elif self.alarm == 3: self.message = "Power Failure - "+('Main' if self.parameter == 1 else low_battery[(self.parameter - 32)])+" Restore"
        elif self.alarm == 4: self.message = "Phone Trouble"+" Restore"
        elif self.alarm == 10: self.message = "Tamper "+str(self.parameter)+" Restore"
        elif self.alarm == 14: self.message = "Siren Tamper"+" Restore"
        elif self.alarm == 22: self.message = "GSM Trouble "+str(self.parameter)+" Restore"
        elif self.alarm == 25: self.message = "Comms Failure RS485 id"+str(self.parameter)+" Restore"

class ComfortV_SystemTypeReport(object):
    def __init__(self, data={}):
        #logger.debug('V? - data: %s', str(data))
        #self.data = int(data[2:4],16)
        self.filesystem = int(data[8:10],16)
        self.version = int(data[4:6],16)
        self.revision = int(data[6:8],16)

class ComfortEXEntryExitDelayStarted(object):
    def __init__(self, data={}):
        self.type = int(data[2:4],16)
        self.delay = int(data[4:6],16)

class Comfort2(mqtt.Client):

    global FIRST_LOGIN
    global RUN


    def init(self, mqtt_ip, mqtt_port, mqtt_username, mqtt_password, comfort_ip, comfort_port, comfort_pincode):
        self.mqtt_ip = mqtt_ip
        self.mqtt_port = mqtt_port
        self.comfort_ip = comfort_ip
        self.comfort_port = comfort_port
        self.comfort_pincode = comfort_pincode
        self.connected = False
        self.username_pw_set(mqtt_username, mqtt_password)

    def handler(signum, frame):                 # Ctrl-Z Keyboard Interrupt
        logger.debug('SIGTSTP (Ctrl-Z) intercepted')

    def sigquit_handler(signum, frame):         # Ctrl-\ Keyboard Interrupt
        global RUN
        logger.debug("SIGQUIT intercepted")
        RUN = False

    signal.signal(signal.SIGTSTP, handler)

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc, properties):

        global RUN
        global BROKERCONNECTED
        global FIRST_LOGIN

        FIRST_LOGIN = True      # Set to True to start refresh on_connect
        
        if rc == 'Success':

            BROKERCONNECTED = True

            #logger.info('MQTT Broker %s (%s)', mqtt_strings[rc], str(rc))
            logger.info('MQTT Broker Connection %s', str(rc))

            time.sleep(0.25)    # Short wait for MQTT to be ready to accept commands.

            # You need to subscribe to your own topics to enable publish messages activating Comfort entities.
            self.subscribe(ALARMCOMMANDTOPIC)
            #self.subscribe(ALARMSTATUSTOPIC)
            #self.subscribe(ALARMBYPASSTOPIC)
            #logger.debug('ALARMNUMBEROFOUTPUTS: %s', str(ALARMNUMBEROFOUTPUTS))
            for i in range(1, ALARMNUMBEROFOUTPUTS + 1):
                self.subscribe(ALARMOUTPUTCOMMANDTOPIC % i)
                time.sleep(0.01)
                #logger.debug('ALARMOUTPUTCOMMANDTOPIC %s', str(ALARMOUTPUTCOMMANDTOPIC % i))
            logger.debug("Subscribed to %d Zone Outputs", ALARMNUMBEROFOUTPUTS)

            for i in ALARMVIRTUALINPUTRANGE: #for virtual inputs #inputs+1 to 128
                #logger.debug('ALARMINPUTCOMMANDTOPIC %s', str(ALARMINPUTCOMMANDTOPIC % i))
                self.subscribe(ALARMINPUTCOMMANDTOPIC % i)
                time.sleep(0.01)
            logger.debug("Subscribed to %d Zone Inputs", ALARMVIRTUALINPUTRANGE[-1])

            for i in ALARMRIOINPUTRANGE: #for inputs 129 to Max Value
                #logger.debug('ALARMRIOINPUTCOMMANDTOPIC %s', str(ALARMRIOINPUTCOMMANDTOPIC % i))
                self.subscribe(ALARMRIOINPUTCOMMANDTOPIC % i)
                time.sleep(0.01)
            if int(COMFORT_RIO_INPUTS) > 0:              
                logger.debug("Subscribed to %d RIO Inputs", ALARMRIOINPUTRANGE[-1] - 128)

            for i in ALARMRIOOUTPUTRANGE: #for outputs 129 to Max Value
                #logger.debug('ALARMRIOOUTPUTCOMMANDTOPIC %s', str(ALARMRIOOUTPUTCOMMANDTOPIC % i))
                self.subscribe(ALARMRIOOUTPUTCOMMANDTOPIC % i)
                time.sleep(0.01)
            if int(COMFORT_RIO_OUTPUTS) > 0:              
                logger.debug("Subscribed to %d RIO Outputs", ALARMRIOOUTPUTRANGE[-1] - 128)

            for i in range(1, ALARMNUMBEROFFLAGS + 1):
                if i >= 255:
                    break
                #logger.debug('ALARMFLAGCOMMANDTOPIC %s', str(ALARMFLAGCOMMANDTOPIC % i))
                self.subscribe(ALARMFLAGCOMMANDTOPIC % i)
                time.sleep(0.01)
            logger.debug("Subscribed to %d Flags", ALARMNUMBEROFFLAGS)
                
                ## Sensors ##
            for i in range(0, ALARMNUMBEROFSENSORS):
                #logger.debug('ALARMSENSORCOMMANDTOPIC %s', str(ALARMSENSORCOMMANDTOPIC % i))
                self.subscribe(ALARMSENSORCOMMANDTOPIC % i)
                time.sleep(0.01)
            logger.debug("Subscribed to %d Sensors", ALARMNUMBEROFSENSORS)

            for i in range(0, ALARMNUMBEROFCOUNTERS + 1):
                self.subscribe(ALARMCOUNTERCOMMANDTOPIC % i)    # Value or Level
                time.sleep(0.01)
                self.subscribe(ALARMCOUNTERSTATETOPIC % i)      # State On=1 or Off=0
                time.sleep(0.01)
            logger.debug("Subscribed to %d Counters", ALARMNUMBEROFCOUNTERS)

            for i in range(1, ALARMNUMBEROFRESPONSES + 1):      # Responses as specified from HA options.
                self.subscribe(ALARMRESPONSECOMMANDTOPIC % i)
                time.sleep(0.01)
            logger.debug("Subscribed to %d Responses", ALARMNUMBEROFRESPONSES)

            if FIRST_LOGIN == True:
                logger.debug("Synchronizing Comfort Data...")
                self.readcurrentstate()
                logger.debug("Synchronization Done.")
            
        else:
            logger.error('MQTT Broker Connection Failed (%s)', str(rc))
            BROKERCONNECTED = False
            #logger.info('MQTT Broker Connection Failed. Check MQTT Broker connection settings')

    def on_disconnect(self, client, userdata, flags, reasonCode, properties):  #client, userdata, flags, reason_code, properties

        global FIRST_LOGIN
        global BROKERCONNECTED

        if reasonCode == 0:
            logger.info('MQTT Broker Disconnect Successfull (%s)', str(reasonCode))
        else:
            #logger.error('MQTT Broker %s', str(rc))
            BROKERCONNECTED = False
            logger.error('MQTT Broker Connection Failed (%s). Check Network or MQTT Broker connection settings', str(reasonCode))
            FIRST_LOGIN = True

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg = 0):

        global SAVEDTIME

        #logger.debug("on_message")
        msgstr = msg.payload.decode()
        #logger.debug(msg.topic+" "+msgstr)
        if msg.topic == ALARMCOMMANDTOPIC:      
            #logger.debug(msg.topic+" "+msgstr)
            if self.connected:
                #logger.debug("msgstr: %s",msgstr)
                if msgstr == "ARM_VACATION":
                    self.comfortsock.sendall(("\x03m!04"+self.comfort_pincode+"\r").encode()) #Local arm to 04 vacation mode. Requires # for open zones
                    SAVEDTIME = datetime.now()
                    self.publish(ALARMSTATETOPIC, "pending",qos=2,retain=False)
                elif msgstr == "ARM_HOME":
                    self.comfortsock.sendall(("\x03m!03"+self.comfort_pincode+"\r").encode()) #Local arm to 03 day mode. Requires # for open zones
                    SAVEDTIME = datetime.now()
                    self.publish(ALARMSTATETOPIC, "pending",qos=2,retain=False)
                elif msgstr == "ARM_NIGHT":
                    self.comfortsock.sendall(("\x03m!02"+self.comfort_pincode+"\r").encode()) #Local arm to 02 night mode. Requires # for open zones
                    SAVEDTIME = datetime.now()
                    self.publish(ALARMSTATETOPIC, "pending",qos=2,retain=False)
                elif msgstr == "ARM_AWAY":
                    self.comfortsock.sendall(("\x03m!01"+self.comfort_pincode+"\r").encode()) #Local arm to 01 away mode. Requires # for open zones + Exit door
                    SAVEDTIME = datetime.now()
                    self.publish(ALARMSTATETOPIC, "pending",qos=2,retain=False)
                elif msgstr == "ARM_CUSTOM_BYPASS":
                    self.comfortsock.sendall("\x03KD1A\r".encode())                           #Send '#' key code (KD1A)
                    SAVEDTIME = datetime.now()
                elif msgstr == "DISARM":
                    self.comfortsock.sendall(("\x03m!00"+self.comfort_pincode+"\r").encode()) #Local arm to 00. disarm mode.
                    SAVEDTIME = datetime.now()
        elif msg.topic.startswith(DOMAIN+"/output") and msg.topic.endswith("/set"):
            #logger.debug("msgstr: %s",msgstr )
            output = int(msg.topic.split("/")[1][6:])
            state = int(msgstr)
            if self.connected:
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
        elif msg.topic.startswith(DOMAIN+"/input") and msg.topic.endswith("/set"):
            virtualinput = int(msg.topic.split("/")[1][5:])
            state = int(msgstr)
            if self.connected:
                self.comfortsock.sendall(("\x03I!%02X%02X\r" % (virtualinput, state)).encode())
                SAVEDTIME = datetime.now()
                #logger.debug("VirtualInput: %s, State: %s",virtualinput,state )
        elif msg.topic.startswith(DOMAIN+"/flag") and msg.topic.endswith("/set"):
            flag = int(msg.topic.split("/")[1][4:])
            state = int(msgstr)
            if self.connected:
                self.comfortsock.sendall(("\x03F!%02X%02X\r" % (flag, state)).encode()) #was F!
                SAVEDTIME = datetime.now()
                #logger.debug("Flag Set: %s, State: %s",flag,state )
        elif msg.topic.startswith(DOMAIN+"/counter") and msg.topic.endswith("/set"): # counter set
            counter = int(msg.topic.split("/")[1][7:])
            if not msgstr.isnumeric() and not msgstr == "ON" and not msgstr == "OFF":
                print("Alphanumeric State detected ('"+str(msgstr)+"'), check MQTT payload configuration for Counter"+str(counter))
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
            #logger.debug("msg.topic: %s",msg.topic)
            sensor = int(msg.topic.split("/")[1][6:])
            state = int(msgstr)
            if self.connected:
                self.comfortsock.sendall(("\x03s!%02X%s\r" % (sensor, self.DecimalToSigned16(state))).encode()) # sensor needs 16 bit signed number
                SAVEDTIME = datetime.now()
                #logger.debug("\x03s!%02X%s\r",sensor, self.DecimalToSigned16(state))

    def DecimalToSigned16(self,value):      # Returns Comfort corrected HEX string value from signed 16-bit decimal value.
        return ('{:04X}'.format((int((value & 0xff) * 0x100 + (value & 0xff00) / 0x100))) )
    
    def CheckZoneNameFormat(self,value):      # Checks CSV file Zone Name to only contain valid characters. Return False if it fails else True
        
        pattern = r'^(?![ ]{1,}).{1}[a-zA-Z0-9_ -]+$'
        return bool(re.match(pattern, value))
    
    def CheckZoneNumberFormat(self,value):      # Checks CSV file Zone Number to only contain valid characters. Return False if it fails else True
        pattern = r'^[0-9]+$'
        if bool(re.match(pattern, value)):
            if value.isnumeric() & (int(value) <= 128):
                return True
            else:
                return False
        else:
            return False
    
    def HexToSigned16Decimal(self,value):        # Returns Signed Decimal value from HEX string EG. FFFF = -1
        #logger.debug("690-HexToSigned16Decimal[value]: %s",value)
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
        #logger.debug("on_publish")
        pass

    def on_subscribe(self, client, userdata, mid, reason_codes, properties):
        for sub_result in reason_codes:
            if sub_result == 1:
                #logger.debug("QoS Value == 1")              # For Information Only
                #logger.debug("on_subscribe")
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

    def readlines(self, recv_buffer=BUFFER_SIZE, delim='\r'):       # Correct string values terminate with 0x0d (CR)

        global FIRST_LOGIN
        global SAVEDTIME
        buffer = ''
        data = True
        while data:
            try:
                data = self.comfortsock.recv(recv_buffer).decode()
            except socket.timeout as e:
                err = e.args[0]
                # this next if/else is a bit redundant, but illustrates how the
                # timeout exception is setup
                if err == 'timed out':
                    #logger.debug("Timeout in readlines(), retry later")
                    self.comfortsock.sendall("\x03cc00\r".encode()) #echo command for keepalive
                    SAVEDTIME = datetime.now()
                    time.sleep(0.1)
                    continue
                else:
                    logger.error ("readlines() error %s", e)
            except socket.error as e:
                # Something else happened, handle error, exit, etc.
                logger.debug("Something else happened %s", e)
                FIRST_LOGIN = True
                raise
            else:
                if len(data) == 0:
                    #logger.debug('data:%s', str(data))
                    logger.debug('Comfort initiated disconnect (LU00).')
                    self.comfortsock.sendall("\x03LI\r".encode()) # Try and gracefully logout if possible.
                    SAVEDTIME = datetime.now()
                    FIRST_LOGIN = True
                else:
                    # got a message do something :)
                    buffer += data

                    while buffer.find(delim) != -1:
                        line, buffer = buffer.split('\r', 1)
                        yield line
        return

    def login(self):
        global SAVEDTIME
        self.comfortsock.sendall(("\x03LI"+self.comfort_pincode+"\r").encode())
        SAVEDTIME = datetime.now()

    def readcurrentstate(self):
        global SAVEDTIME
        if self.connected == True:

            #get Comfort type
            self.comfortsock.sendall("\x03V?\r".encode())
            SAVEDTIME = datetime.now()
            time.sleep(0.1)
            #get Security Mode
            self.comfortsock.sendall("\x03M?\r".encode())
            SAVEDTIME = datetime.now()
            time.sleep(0.1)
            #get all zone input states
            self.comfortsock.sendall("\x03Z?\r".encode())
            SAVEDTIME = datetime.now()
            time.sleep(0.1)
            #get all SCS/RIO input states
            self.comfortsock.sendall("\x03z?\r".encode())
            SAVEDTIME = datetime.now()
            time.sleep(0.1)
            #get all output states
            self.comfortsock.sendall("\x03Y?\r".encode())
            SAVEDTIME = datetime.now()
            time.sleep(0.1)
            #get all RIO output states
            self.comfortsock.sendall("\x03y?\r".encode())       # Request/Report all RIO Outputs
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
            self.comfortsock.sendall("\x03a?\r".encode())       # a? Status Request
            SAVEDTIME = datetime.now()
            time.sleep(0.1)
            #get Bypassed Zones
            self.comfortsock.sendall("\x03b?00\r".encode())       # b?00 Bypassed Zones
            SAVEDTIME = datetime.now()
            time.sleep(0.1)

            #get all sensor values. 0 - 31
            self.comfortsock.sendall("\x03r?010010\r".encode())
            SAVEDTIME = datetime.now()
            time.sleep(0.1)
            self.comfortsock.sendall("\x03r?011010\r".encode())
            SAVEDTIME = datetime.now()
            time.sleep(0.1)

            #Clear all Timer Reports
            for i in range(1, 65):
                self.publish(ALARMTIMERREPORTTOPIC % i, 0,qos=2,retain=False)
                time.sleep(0.01)

          #get all counter values
            for i in range(0, int((ALARMNUMBEROFCOUNTERS+1) / 16)):          # Counters 0 to 254 Using 256/16 = 16 iterations
                #logger.debug("self.comfortsock.sendall(r?00%X010.encode()" % (i))
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
            #self.publish(ALARMEXTMESSAGETOPIC, "",qos=2,retain=True)    # Emptry string removes topic. For future development !!!

    def setdatetime(self):
        global SAVEDTIME
        if self.connected == True:  #set current date and time if COMFORT_TIME Flag is set to True
            #logger.debug('COMFORT_TIME=%s', COMFORT_TIME)
            if COMFORT_TIME == 'True':
                logger.info('Setting Comfort Date/Time')
                now = datetime.now()
                self.comfortsock.sendall(("\x03DT%02d%02d%02d%02d%02d%02d\r" % (now.year, now.month, now.day, now.hour, now.minute, now.second)).encode())
                SAVEDTIME = datetime.now()

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
        
        logger.debug("SIGNUM: %s received", str(signum))
        
        if self.connected == True:
            self.comfortsock.sendall("\x03LI\r".encode()) #Logout command.
            SAVEDTIME = datetime.now()
        if BROKERCONNECTED == True:      # MQTT Connected
            infot = self.publish(ALARMAVAILABLETOPIC, 0,qos=2,retain=True)
            infot = self.publish(ALARMLWTTOPIC, 'Offline',qos=2,retain=True)
            infot.wait_for_publish()
        RUN = False
        exit(0)

    def run(self):

        global FIRST_LOGIN         # Used to track if Addon started up or not.
        global RUN
        global SAVEDTIME
        global TIMEOUT
        global BROKERCONNECTED
        global ZONEMAPFILE

        signal.signal(signal.SIGTERM, self.exit_gracefully)
        signal.signal(signal.SIGQUIT, self.exit_gracefully)

        zonemap = Path("/config/zones.csv")
        
        if zonemap.is_file():
            file_stats = os.stat(zonemap)
            if file_stats.st_size > 5120:
                logger.warning ("Suspicious Zone Mapping File detected. Size is larger than anticipated. (%s Bytes)", file_stats.st_size) 
                ZONEMAPFILE = False
            else:
                logger.info ("Zone Mapping File detected, %s Bytes", file_stats.st_size) 
               
                # Initialize an empty dictionary
                self.zone_to_name = {}

                # Open the CSV file
                with open(zonemap, newline='') as csvfile:
                    # Create a CSV reader object
                    reader = csv.DictReader(csvfile)
    
                    # Iterate over each row in the CSV file
                    for row in reader:
                        # Truncate the 'zone' numeric value to 3 characters (0-999) and 'name' to 30 characters. 

                        if self.CheckZoneNumberFormat(row['zone'][:3]):
                            zone = row['zone'][:3]          # Check Zone Number sanity else blank.
                            ZONEMAPFILE = True              # File available and data read into dictionary 'data'
                        else: 
                            zone = ""
                            logger.error("Invalid Zone Number detected in 'zones.csv' file, file ignored.")
                            ZONEMAPFILE = False
                            break

                        if self.CheckZoneNameFormat(row['name'][:30]): 
                            name = row['name'][:30]         # Check Zone sanity else blank.
                            ZONEMAPFILE = True              # File available and data read into dictionary 'data'
                        else: 
                            name = ""
                            logger.error("Invalid Zone Name detected in 'zones.csv' file, file ignored.")
                            ZONEMAPFILE = False             # File available and data read into dictionary 'data'
                            break

                        # Add the truncated value to the dictionary
                        self.zone_to_name[zone] = name

        self.connect_async(self.mqtt_ip, self.mqtt_port, 60)
        #logging.debug("MQTT Broker Connected: %s", str(self.connected))
        if self.connected == True:
            BROKERCONNECTED = True
            self.publish(ALARMAVAILABLETOPIC, 0,qos=2,retain=True)
            self.will_set(ALARMLWTTOPIC, payload="Offline", qos=2, retain=True)
        self.loop_start()   

        try:
            while RUN:
                try:
                    self.comfortsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    logger.info('Connecting to Comfort (%s) on port %s', self.comfort_ip, str(self.comfort_port) )
                    self.comfortsock.connect((self.comfort_ip, self.comfort_port))
                    self.comfortsock.settimeout(TIMEOUT.seconds)
                    self.login()
                    for line in self.readlines():
                        if line[1:] != "cc00":
                            logger.debug(line[1:])  	    # Print all responses only in DEBUG mode. Print all received Comfort commands except keepalives.

                            if datetime.now() > SAVEDTIME + TIMEOUT:            #
                                self.comfortsock.sendall("\x03cc00\r".encode()) # Keepalive check when data comes in.
                                SAVEDTIME = datetime.now()                      # Update SavedTime variable
                                time.sleep(0.1)

                        #if self.check_string(line[:3]):     # Check for "\x03":   #check for valid prefix now and a-zA-Z following character.
                        if self.check_string(line):         # Check for "(\x03[a-zA-Z0-9]*)$" in complete line.
                            pattern = re.compile(r'(\x03[a-zA-Z0-9!?]*)$')      # Extract 'legal' characters from line.
                            match = re.search(pattern, line)
                            line = match.group(1)
                            if line[1:3] == "LU":
                                luMsg = ComfortLUUserLoggedIn(line[1:])
                                if luMsg.user != 0:
                                    logger.info('Comfort Login Ok - User %s', (luMsg.user if luMsg.user != 254 else 'Engineer'))

                                    if BROKERCONNECTED == True:     # Settle time for Comfort.
                                        time.sleep(1)
                                    else:
                                        logger.info("Waiting for MQTT Broker to come Online...")

                                    self.connected = True  
                                    self.publish(ALARMCOMMANDTOPIC, "comm test",qos=2,retain=True)
                                    self.setdatetime()      # Set Date/Time if Option is enabled

                                    if FIRST_LOGIN == True:
                                        self.readcurrentstate()
                                        FIRST_LOGIN = False
                                else:
                                    logger.debug("Disconnect (LU00) Received from Comfort.")
                                    FIRST_LOGIN = True
                                    break
                            elif line[1:5] == "PS00":       # Set Date/Time once a day on receipt of PS command. Usually midnight or any time the system is armed.
                                self.setdatetime()          # Set Date/Time if Flag is set at 00:00 every day if option is enabled.
                            elif line[1:3] == "IP":
                                ipMsg = ComfortIPInputActivationReport(line[1:])
                                #logger.debug("Input State: %d", ipMsg.state)
                                if ipMsg.state < 2:
                                    self.publish(ALARMINPUTTOPIC % ipMsg.input, ipMsg.state,qos=2,retain=True)
                                    #logger.debug("Input State: %d", ipMsg.state)
                            elif line[1:3] == "CT":
                                ipMsgCT = ComfortCTCounterActivationReport(line[1:])
                                self.publish(ALARMCOUNTERINPUTRANGE % ipMsgCT.counter, ipMsgCT.value,qos=2,retain=True)     # Value Information
                                time.sleep(0.01)
                                self.publish(ALARMCOUNTERSTATETOPIC % ipMsgCT.counter, ipMsgCT.state,qos=2,retain=True)     # State Information
                            elif line[1:3] == "s?":
                                ipMsgSQ = ComfortCTCounterActivationReport(line[1:])
                                self.publish(ALARMSENSORTOPIC % ipMsgSQ.counter, ipMsgSQ.state)
                            elif line[1:3] == "sr":
                                ipMsgSR = ComfortCTCounterActivationReport(line[1:])
                                self.publish(ALARMSENSORTOPIC % ipMsgSR.counter, ipMsgSR.state)
                            elif line[1:3] == "TR":
                                ipMsgTR = ComfortCTCounterActivationReport(line[1:])
                                self.publish(ALARMTIMERREPORTTOPIC % ipMsgTR.counter, ipMsgTR.state,qos=2,retain=False)
                            elif line[1:3] == "Z?":                             # Zones/Inputs
                                zMsg = ComfortZ_ReportAllZones(line[1:])
                                for ipMsgZ in zMsg.inputs:
                                    self.publish(ALARMINPUTTOPIC % ipMsgZ.input, ipMsgZ.state, retain=False)
                                    time.sleep(0.01)    # 10mS delay between commands
                                logger.debug("Max. Reported Zones/Inputs: %d", zMsg.max_zones)
                                if zMsg.max_zones < int(COMFORT_INPUTS):
                                    logger.warning("Max. Reported Zone Inputs of %d is less than the configured value of %s", zMsg.max_zones, COMFORT_INPUTS)
                            elif line[1:3] == "z?":                             # SCS/RIO Inputs
                                zMsg = Comfort_Z_ReportAllZones(line[1:])
                                for ipMsgZ in zMsg.inputs:
                                    self.publish(ALARMINPUTTOPIC % ipMsgZ.input, ipMsgZ.state)
                                    time.sleep(0.01)    # 10mS delay between commands
                                logger.debug("Max. Reported SCS/RIO Inputs: %d", zMsg.max_zones)
                            elif line[1:3] == "M?" or line[1:3] == "MD":
                                mMsg = ComfortM_SecurityModeReport(line[1:])
                                self.publish(ALARMSTATETOPIC, mMsg.modename,qos=2,retain=False)      # Was True
                                self.entryexitdelay = 0                         #zero out the countdown timer
                            elif line[1:3] == "S?":
                                SMsg = ComfortS_SecurityModeReport(line[1:])
                                self.publish(ALARMSTATUSTOPIC, SMsg.modename,qos=2,retain=True)
                            elif line[1:3] == "V?":
                                VMsg = ComfortV_SystemTypeReport(line[1:])
                                if VMsg.filesystem != 34:
                                    logging.warning("Unsupported Comfort System detected (File System %d).", VMsg.filesystem)
                                else:
                                    logging.info("Comfort II Ultra detected (Firmware %d.%03d)", VMsg.version, VMsg.revision)
                            elif line[1:3] == "a?":     # Not Implemented. For Future Development !!!
                                aMsg = Comfort_A_SecurityInformationReport(line[1:])
                                if aMsg.type == 'LowBattery':
                                    logging.debug("Low Battery %s", aMsg.battery)
                            elif line[1:3] == "ER":           
                                erMsg = ComfortERArmReadyNotReady(line[1:])
                                if not erMsg.zone == 0:

                                    if ZONEMAPFILE & self.CheckZoneNumberFormat(str(erMsg.zone)):
                                        logging.warning("Zone %s Not Ready (%s)", str(erMsg.zone), self.zone_to_name.get(str(erMsg.zone),'N/A'))
                                    else: 
                                        logging.warning("Zone %s Not Ready", str(erMsg.zone))

                                    message_topic = "Zone "+str(erMsg.zone)+ " Not Ready"
                                    self.publish(ALARMMESSAGETOPIC, message_topic, qos=2, retain=True)          # Empty string removes topic.
                                    #self.publish(ALARMSTATETOPIC, "pending",qos=2,retain=False)                 # This is the correct state for Open Zones but it removes the buttons
                                                                                                                # from the Keypad so you can't press '#'
                                else:
                                    logging.info("Ready To Arm...")
                                    # Sending KD1A when receiving ER message confuses Comfort. When arming local to any mode it immediately goes into Arm Mode
                                    # Not all Zones are announced and it 'presses' the '#' key on your behalf.
                                    # self.comfortsock.sendall("\x03KD1A\r".encode()) #Force Arm, acknowledge Open Zones and Bypasses them.
                            elif line[1:3] == "AM":
                                amMsg = ComfortAMSystemAlarmReport(line[1:])
                                #logging.info("Message: %s", amMsg.message)
                                self.publish(ALARMMESSAGETOPIC, amMsg.message, qos=2, retain=True)
                                if amMsg.triggered:
                                    self.publish(ALARMSTATETOPIC, "triggered", qos=2, retain=False)     # Original message
                            elif line[1:3] == "AR":
                                arMsg = ComfortARSystemAlarmReport(line[1:])
                                self.publish(ALARMMESSAGETOPIC, arMsg.message,qos=2,retain=True)
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
                            elif line[1:3] == "OP":
                                ipMsg = ComfortOPOutputActivationReport(line[1:])
                                self.publish(ALARMOUTPUTTOPIC % ipMsg.output, ipMsg.state,qos=2,retain=True)
                            elif line[1:3] == "Y?":     # Comfort Outputs
                                yMsg = ComfortY_ReportAllOutputs(line[1:])
                                for opMsgY in yMsg.outputs:
                                    self.publish(ALARMOUTPUTTOPIC % opMsgY.output, opMsgY.state,qos=2,retain=True)
                                    time.sleep(0.01)    # 10mS delay between commands
                                logger.debug("Max. Reported Outputs: %d", yMsg.max_zones)
                                if yMsg.max_zones < int(COMFORT_OUTPUTS):
                                    logger.warning("Max. Reported Outputs of %d is less than the configured value of %s", yMsg.max_zones, COMFORT_OUTPUTS)
                            elif line[1:3] == "y?":     # SCS/RIO Outputs
                                yMsg = Comfort_Y_ReportAllOutputs(line[1:])
                                for opMsgY in yMsg.outputs:
                                    self.publish(ALARMOUTPUTTOPIC % opMsgY.output, opMsgY.state)
                                    time.sleep(0.01)    # 10mS delay between commands
                                logger.debug("Max. Reported SCS/RIO Outputs: %d", yMsg.max_zones)
                            elif line[1:5] == "r?00":
                                cMsg = Comfort_R_ReportAllSensors(line[1:])
                                for cMsgr in cMsg.counters:
                                    self.publish(ALARMCOUNTERINPUTRANGE % cMsgr.counter, cMsgr.value,qos=2,retain=True)     # Value Information
                                    time.sleep(0.01)    # 10mS delay between commands
                                    self.publish(ALARMCOUNTERSTATETOPIC % cMsgr.counter, cMsgr.state,qos=2,retain=True)     # State Information
                                    time.sleep(0.01)    # 10mS delay between commands
                            elif line[1:5] == "r?01":
                                sMsg = Comfort_R_ReportAllSensors(line[1:])
                                for sMsgr in sMsg.sensors:
                                    self.publish(ALARMSENSORTOPIC % sMsgr.sensor, sMsgr.value,qos=2,retain=False)           # Was True, test False
                                    time.sleep(0.01)    # 10mS delay between commands
                            elif (line[1:3] == "f?") and (len(line) == 69):
                                fMsg = Comfortf_ReportAllFlags(line[1:])
                                for fMsgf in fMsg.flags:
                                    self.publish(ALARMFLAGTOPIC % fMsgf.flag, fMsgf.state,qos=2,retain=True)
                                    time.sleep(0.01)    # 10mS delay between commands
                            elif (line[1:3] == "b?"):   # and (len(line) == 69):
                                bMsg = ComfortB_ReportAllBypassZones(line[1:])
                                if bMsg.value == "-1":
                                    logger.debug("Zones Bypassed: <None>")
                                    self.publish(ALARMBYPASSTOPIC, -1, qos=2, retain=True)
                                else:
                                    logger.debug("Zones Bypassed: %s", bMsg.value)
                                    self.publish(ALARMBYPASSTOPIC, bMsg.value, qos=2,retain=True)
                                for bMsgb in bMsg.zones:
                                    self.publish(ALARMINPUTBYPASSTOPIC % bMsgb.zone, bMsgb.state,qos=2,retain=True)
                                    time.sleep(0.01)    # 10mS delay between commands
                            elif line[1:3] == "FL":
                                flMsg = ComfortFLFlagActivationReport(line[1:])
                                self.publish(ALARMFLAGTOPIC % flMsg.flag, flMsg.state,qos=2,retain=True)
                            elif line[1:3] == "BY":
                                byMsg = ComfortBYBypassActivationReport(line[1:])   
                                if byMsg.state == 1:
                                    if ZONEMAPFILE & self.CheckZoneNumberFormat(str(byMsg.zone)):
                                        logging.warning("Zone %s Bypassed (%s)", str(byMsg.zone), self.zone_to_name.get(str(byMsg.zone),'N/A'))
                                    else: logging.warning("Zone %s Bypassed", str(byMsg.zone))
                                else:
                                    if ZONEMAPFILE & self.CheckZoneNumberFormat(str(byMsg.zone)):
                                        logging.info("Zone %s Unbypassed (%s)", str(byMsg.zone), self.zone_to_name.get(str(byMsg.zone),'N/A'))
                                    else: logging.info("Zone %s Unbypassed", str(byMsg.zone))

                                self.publish(ALARMINPUTBYPASSTOPIC % byMsg.zone, byMsg.state, qos=2, retain=True)
                                time.sleep(0.01)    # 10mS delay between commands
                                self.publish(ALARMBYPASSTOPIC, byMsg.value, qos=2,retain=True)
                                time.sleep(0.01)    # 10mS delay between commands

                            elif line[1:3] == "RS":
                                #on rare occassions comfort ucm might get reset (RS11), our session is no longer valid, need to relogin
                                logger.warning('Reset detected')
                                self.login()
                            else:
                                if datetime.now() > (SAVEDTIME + TIMEOUT):  # If no command sent in 2 minutes then send keepalive.
                                    #logger.debug("Sending Keepalives")
                                    self.comfortsock.sendall("\x03cc00\r".encode()) #echo command for keepalive
                                    SAVEDTIME = datetime.now()
                                    time.sleep(0.1)
                        else:
                            logger.warning("Invalid response received (%s)", line.encode())

                except socket.error as v:
                    ##errorcode = v[0]
                    logger.error('Comfort Socket Error %s', str(v))
                    ##raise
                logger.error('Lost connection to Comfort, reconnecting...')
                if BROKERCONNECTED == True:      # MQTT Connected ??
                    self.publish(ALARMAVAILABLETOPIC, 0,qos=2,retain=True)
                    self.publish(ALARMLWTTOPIC, 'Offline',qos=2,retain=True)
                time.sleep(RETRY.seconds)
        except KeyboardInterrupt as e:
            logger.debug("SIGINT (Ctrl-C) Intercepted")
            logger.info('Shutting down.')
            if self.connected == True:
                self.comfortsock.sendall("\x03LI\r".encode()) #Logout command.
            RUN = False
        finally:
            if BROKERCONNECTED == True:      # MQTT Connected ??
                infot = self.publish(ALARMAVAILABLETOPIC, 0,qos=2,retain=True)
                infot = self.publish(ALARMLWTTOPIC, 'Offline',qos=2,retain=True)
                infot.wait_for_publish(1)


mqttc = Comfort2(mqtt.CallbackAPIVersion.VERSION2, mqtt_client_id, transport=MQTT_PROTOCOL)
mqttc.init(MQTTBROKERIP, MQTTBROKERPORT, MQTTUSERNAME, MQTTPASSWORD, COMFORTIP, COMFORTPORT, PINCODE)
mqttc.run()
