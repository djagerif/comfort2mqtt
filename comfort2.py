# Original Copyright(c) 2018 Khor Chin Heong (koochyrat@gmail.com)
# Modified by Ingo de Jager 2023 (ingodejager@gmail.com)
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

#import os
import re
#from re import DEBUG
#import select
import socket
import time
import datetime
import threading
import logging
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
from argparse import ArgumentParser

DOMAIN = "comfort2"
ALARMSTATETOPIC = DOMAIN+"/alarm"
ALARMCOMMANDTOPIC = DOMAIN+"/alarm/set"
ALARMAVAILABLETOPIC = DOMAIN+"/alarm/online"
ALARMLWTTOPIC = DOMAIN+"/alarm/LWT"
ALARMMESSAGETOPIC = DOMAIN+"/alarm/message"
ALARMTIMERTOPIC = DOMAIN+"/alarm/timer"
ALARMDOORBELLTOPIC = DOMAIN+"/doorbell"

FIRST_LOGIN = 1

mqtt_strings = ['Connection successful',
				'Connection refused - incorrect protocol version',
				'Connection refused - invalid client identifier',
				'Connection refused - server unavailable',
				'Connection refused - malformed username or password',
				'Connection refused - not authorised',
				'Connection lost or bad',
				'Timeout waiting for Length bytes',
				'Timeout waiting for Payload',
				'Timeout waiting for CONNACK',
				'Timeout waiting for SUBACK',
				'Timeout waiting for UNSUBACK',
				'Timeout waiting for PINGRESP',
				'Malformed Remaining Length',
				'Problem with the underlying communication port',
				'Address could not be parsed',
				'Malformed received MQTT packet',
				'Subscription failure',
				'Payload decoding failure',
				'Failed to compile a Decoder',
				'The received MQTT packet type is not supported on this client',
				'Timeout waiting for PUBACK',
				'Timeout waiting for PUBREC',
				'Timeout waiting for PUBCOMP']

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
    '--alarm-flags',
    type=int, default=0,
    help='Number of Flags')

group.add_argument(
    '--alarm-counters',
    type=int, default=0,
    help='Number of Counters')

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

#logger.setLevel(option.verbosity)
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=option.verbosity,
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger.info('Importing the add-on configuration options')

MQTT_USER=option.broker_username
MQTT_PASSWORD=option.broker_password
MQTT_SERVER=option.broker_address
MQTT_PORT=option.broker_port
COMFORT_ADDRESS=option.comfort_address
COMFORT_PORT=option.comfort_port
COMFORT_LOGIN_ID=option.comfort_login_id
MQTT_LOG_LEVEL=option.verbosity
COMFORT_INPUTS=int(option.alarm_inputs)
COMFORT_OUTPUTS=int(option.alarm_outputs)
COMFORT_RESPONSES=int(option.alarm_responses)
COMFORT_FLAGS=int(option.alarm_flags)
COMFORT_COUNTERS=int(option.alarm_counters)
COMFORT_TIME=str(option.comfort_time)
COMFORT_RIO_INPUTS=str(option.alarm_rio_inputs)
COMFORT_RIO_OUTPUTS=str(option.alarm_rio_outputs)


#MQTT_USER=$(bashio::config 'mqtt_user')
#MQTT_PASSWORD=$(bashio::config 'mqtt_password')
#MQTT_SERVER=$(bashio::config 'mqtt_broker_address')
#MQTT_PORT=$(bashio::config 'mqtt_broker_port')
#COMFORT_ADDRESS=$(bashio::config 'comfort_address')
#COMFORT_PORT=$(bashio::config 'comfort_port')
#COMFORT_LOGIN_ID=$(bashio::config 'comfort_login_id')
#MQTT_CA_CERT_PATH=$(bashio::config 'broker_ca')
#MQTT_CLIENT_CERT_PATH=$(bashio::config 'broker_client_cert')
#MQTT_CLIENT_KEY_PATH=$(bashio::config 'broker_client_key')
#MQTT_LOG_LEVEL=$(bashio::config 'log_verbosity')

#Todo: Set Number of Zones and calculate virtual zones.

ALARMINPUTTOPIC = DOMAIN+"/input%d"   #input1,input2,... input128 for every input. Physical Inputs (Default 8), Max 128
ALARMVIRTUALINPUTRANGE = range(1,int(COMFORT_INPUTS)+1)   #set this according to your system. Starts at 1 -> {value}
ALARMINPUTCOMMANDTOPIC = DOMAIN+"/input%d/set"   #input1,input2,... input128 for virtual inputs

ALARMRIOINPUTTOPIC = DOMAIN+"/input%d"   #input129,input130,... input248 for every input. Physical SCS/RIO Inputs (Default 0), Max 120  
ALARMRIOINPUTRANGE = range(129,129+int(COMFORT_RIO_INPUTS))   #set this according to your system. Starts at 129 -> 248 (Max.)
ALARMRIOINPUTCOMMANDTOPIC = DOMAIN+"/input%d/set"   #input129,input130,... input248 for SCS/RIO inputs. Cannot set as Virtual Input.

ALARMOUTPUTTOPIC = DOMAIN+"/output%d" #output1,output2,... for every output
ALARMNUMBEROFOUTPUTS = COMFORT_OUTPUTS    #set this according to your system. Physical Outputs (Default 0), Max 96
ALARMOUTPUTCOMMANDTOPIC = DOMAIN+"/output%d/set" #output1/set,output2/set,... for every output

ALARMRIOOUTPUTTOPIC = DOMAIN+"/output%d" #output129,output130,... for every SCS/RIO output
ALARMRIOOUTPUTRANGE = range(129,129+int(COMFORT_RIO_OUTPUTS))    #set this according to your system. Physical SCS/RIO Outputs (Default 0), Max 120
ALARMRIOOUTPUTCOMMANDTOPIC = DOMAIN+"/output%d/set" #output129,output130,... output248 for SCS/RIO outputs.

ALARMNUMBEROFRESPONSES = COMFORT_RESPONSES    #set this according to your system. Default 0, Max 1024
ALARMRESPONSECOMMANDTOPIC = DOMAIN+"/response%d/set" #response1,response2,... for every response

ALARMNUMBEROFFLAGS = COMFORT_FLAGS    #set this according to your system. Default 254 (1-254), Max 254
ALARMFLAGTOPIC = DOMAIN+"/flag%d"   #flag1,flag2,...flag254
ALARMFLAGCOMMANDTOPIC = DOMAIN+"/flag%d/set" #flag1/set,flag2/set,... flag254/set

ALARMNUMBEROFSENSORS = 32       # Use system default = 32 (0-31)
ALARMSENSORTOPIC = DOMAIN+"/sensor%d"   #sensor0,sensor1,...sensor31
ALARMSENSORCOMMANDTOPIC = DOMAIN+"/sensor%d/set" #sensor0,sensor1,...sensor31

ALARMNUMBEROFCOUNTERS = 255 #COMFORT_COUNTERS        # set according to system. Default 255 (0-254), Max 255
ALARMCOUNTERINPUTRANGE = DOMAIN+"/counter%d"  #each counter represents a value
ALARMCOUNTERCOMMANDTOPIC = DOMAIN+"/counter%d/set" # set the counter to a value for between 0 (off) to 255 (full on) or any 16-bit value.

ALARMTIMERTOPIC = DOMAIN+"/timer%d"             #each timer instance.
ALARMNUMBEROFTIMERS = 64                        # default timer instances. 1 - 64.

logger.info('Completed importing addon configuration options')
#print ("")

# The following variables values were passed through via the Home Assistant add on configuration options
logger.debug('The following variable values were passed through via the Home Assistant add on configuration options')
logger.debug('MQTT_USER = %s', MQTT_USER)
logger.debug('MQTT_PASSWORD = ******')
logger.debug('MQTT_SERVER = %s', MQTT_SERVER)
logger.debug('MQTT_PORT = %s', MQTT_PORT)
logger.debug('COMFORT_ADDRESS = %s', COMFORT_ADDRESS)
logger.debug('COMFORT_PORT = %s', COMFORT_PORT)
logger.debug('COMFORT_LOGIN_ID = ******')
#logger.debug('MQTT_CA_CERT_PATH = %s', MQTT_CA_CERT_PATH)
#logger.debug('MQTT_CLIENT_CERT_PATH = %s', MQTT_CLIENT_CERT_PATH)
#logger.debug('MQTT_CLIENT_KEY_PATH = %s', MQTT_CLIENT_KEY_PATH)
logger.debug('MQTT_LOG_LEVEL = %s', MQTT_LOG_LEVEL)
logger.debug('COMFORT_INPUTS= %s', COMFORT_INPUTS)
logger.debug('COMFORT_OUTPUTS= %s', COMFORT_OUTPUTS)
logger.debug('COMFORT_RIO_INPUTS= %s', COMFORT_RIO_INPUTS)
logger.debug('COMFORT_RIO_OUTPUTS= %s', COMFORT_RIO_OUTPUTS)
logger.debug('COMFORT_RESPONSES= %s', COMFORT_RESPONSES)
logger.debug('COMFORT_FLAGS= %s', COMFORT_FLAGS)
logger.debug('COMFORT_COUNTERS= %s', COMFORT_COUNTERS)
logger.debug('COMFORT_TIME= %s', COMFORT_TIME)

# Map HA variables to internal variables.

MQTTBROKERIP = MQTT_SERVER
MQTTBROKERPORT = int(MQTT_PORT)
MQTTUSERNAME = MQTT_USER
MQTTPASSWORD = MQTT_PASSWORD
COMFORTIP = COMFORT_ADDRESS
COMFORTPORT = int(COMFORT_PORT)
PINCODE = COMFORT_LOGIN_ID

# Used by Docker, please comment out below if HA above is used.

#MQTTBROKERIP = os.environ['MQTTBROKERIP']
#MQTTBROKERPORT = int(os.environ['MQTTBROKERPORT'])
#MQTTUSERNAME = os.environ['MQTTUSERNAME']
#MQTTPASSWORD = os.environ['MQTTPASSWORD']
#COMFORTIP = os.environ['COMFORTIP']
#COMFORTPORT = int(os.environ['COMFORTPORT'])
#PINCODE = os.environ['COMFORTPIN']

BUFFER_SIZE = 4096
TIMEOUT = timedelta(seconds=30) #Comfort will disconnect if idle for 120 secs, so make sure this is less than that
RETRY = timedelta(seconds=10)

class ComfortLUUserLoggedIn(object):
    def __init__(self, datastr="", user=0):
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
    def __init__(self, datastr="", counter=0, state=0):
        #logger.debug("ComfortCTCounterActivationReport[datastr]: %s, [counter]: %s, [state]: %s", datastr, counter, state)
        if datastr:
            self.counter = int(datastr[2:4], 16)    #Integer value 3
            #logger.debug("ComfortCTCounterActivationReport[counter(int)]: %s", self.counter)
            #self.state = self.ComfortSigned16(datastr[4:6]+datastr[6:8])                                # Use 16-bit format
            self.state = self.ComfortSigned16(int("%s%s" % (datastr[6:8], datastr[4:6]),16))    # Use new 16-bit format
            #self.state = self.ComfortSigned16(hex(int("%s%s" % (datastr[6:8], datastr[4:6]),16)))       # Use new 16-bit format        state = FF7F
            #logger.debug("ComfortCTCounterActivationReport[state(int)]: %s", self.state)
        else:
            self.counter = counter
            self.state = state
            #self.state = self.byte_swap_16_bit(state)

    def ComfortSigned16(self,value):     # Returns signed 16-bit value where required.
        return -(value & 0x8000) | (value & 0x7fff)
    
    #def ComfortSigned16(self,value):     # Returns signed 16-bit value where required.
    #    #logger.debug("#313 ComfortSigned16[value]: %s", value)
    #    value = self.byte_swap_16_bit(value)
    #    #logger.debug("#315 ComfortSigned16[value]: %s", value[2:].zfill(4))
    #    #return -(value & 0x8000) | (value & 0x7fff)
    #    return self.HexToSigned16Decimal(value[2:].zfill(4))

### Add Byte-Swap code below ###
    def HexToSigned16Decimal(self,value):        # Returns Signed Decimal value from HEX string EG. FFFF = -1
        #logger.debug("#321 HexToSigned16Decimal[value]: %s", value)
        return -(int(value,16) & 0x8000) | (int(value,16) & 0x7fff)

    def byte_swap_16_bit(self, hex_string):
        # Ensure the string is prefixed with '0x' for hex conversion
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

class ComfortZ_ReportAllZones(object):
    def __init__(self, data={}):
        self.inputs = []
        b = (len(data) - 2) // 2   #variable number of zones reported
        for i in range(1,b+1):
            inputbits = int(data[2*i:2*i+2],16)
            for j in range(0,8):
                self.inputs.append(ComfortIPInputActivationReport("", 8*(i-1)+1+j,(inputbits>>j) & 1))

class Comfort_Z_ReportAllZones(object):     #SCS/RIO z?
    def __init__(self, data={}):
        self.inputs = []    
        b = (len(data) - 2) // 2   #variable number of zones reported
        for i in range(1,b+1):  
            inputbits = int(data[2*i:2*i+2],16)
            for j in range(0,8): 
                self.inputs.append(ComfortIPInputActivationReport("", 128+8*(i-1)+1+j,(inputbits>>j) & 1))

class Comfort_RSensorActivationReport(object):
    def __init__(self, datastr="", sensor=0, state=0):
        if datastr:
            self.sensor = int(datastr[2:4], 16)
            #self.state = int(datastr[4:6], 16)
            self.value = self.ComfortSigned16(int("%s%s" % (datastr[6:8], datastr[4:6]),16))    # Use new 16-bit format
            #print("self.state:%s" % (self.ComfortSigned16(int("%s%s" % (datastr[6:8], datastr[4:6]),16))))
        else:
            self.sensor = sensor
            self.value = state

    def ComfortSigned16(self,value):     # Returns signed 16-bit value where required.
        return -(value & 0x8000) | (value & 0x7fff)

class Comfort_R_ReportAllSensors(object):
    def __init__(self, data={}, sensor=0, value=0, counter=0):
        #logger.debug("ReportAllSensors(data): %s", data)
        self.sensors = []
        self.counters = []
        b = (len(data) - 8) // 4   #Fixed number of sensors reported from r?01 command. 0-15 and 16-31.
        self.RegisterStart = int(data[4:6],16)
        self.RegisterType = int(data[2:4],16)
        #logger.debug("len(data) - 8 // 4: %s", b)
        #logger.debug("RegisterStart: %s", self.RegisterStart)
        #logger.debug("RegisterType: %s", self.RegisterType)
        for i in range(0,b):
            if self.RegisterType == 1:  #Sensor
                sensorbits = data[8+(4*i):8+(4*i)+4]        #0000
                
                #Swap bits here.
                #Change to Signed value here.
                #self.value = int("%s%s" % (sensorbits[2:4], sensorbits[0:2]),16)
                self.value = int((sensorbits[2:4] + sensorbits[0:2]),16)
                
                self.sensor =  self.RegisterStart+i
                #logger.debug("Type:%d, Sensor:%s, Integer Value:%s" % (self.RegisterType, self.sensor, self.value))
                self.sensors.append(Comfort_RSensorActivationReport("", self.RegisterStart+i, self.value))
            else:   # Should be '0' or Counter
                counterbits = data[8+(4*i):8+(4*i)+4]   #0000
                #logger.debug("counterbits: %s", counterbits)
                self.value = int((counterbits[2:4] + counterbits[0:2]),16)
                self.counter = self.RegisterStart+i
                self.counters.append(ComfortCTCounterActivationReport("", self.RegisterStart+i, self.value))
            #    #print("Type:%d, Register:%d, Inputbits:%d" % (self.RegisterType, self.RegisterStart+i, value))
    
    def ComfortSigned16(self,value):     # Returns signed 16-bit value from HEX value.
        return -(value & 0x8000) | (value & 0x7fff)


class ComfortY_ReportAllOutputs(object):
    def __init__(self, data={}):
        self.outputs = []
        b = (len(data) - 2) // 2   #variable number of outputs reported
        for i in range(1,b+1):
            outputbits = int(data[2*i:2*i+2],16)
            for j in range(0,8):
                self.outputs.append(ComfortOPOutputActivationReport("", 8*(i-1)+1+j,(outputbits>>j) & 1))

class Comfort_Y_ReportAllOutputs(object): 
    def __init__(self, data={}):    
        self.outputs = []           
        b = (len(data) - 2) // 2   #variable number of outputs reported
        for i in range(1,b+1):  
            outputbits = int(data[2*i:2*i+2],16)
            for j in range(0,8):
                self.outputs.append(ComfortOPOutputActivationReport("", 128+8*(i-1)+1+j,(outputbits>>j) & 1))

#class Comfortf_ReportAllFlags(object):
#    def __init__(self, data={}):
#        self.flags = []         
#        b = (len(data) - 4) // 2   #b = 32
#        for i in range(2,b+2):      
#            flagbits = int(data[2*i:2*i+2],16)
#            #print ("flagbits: %d" % (flagbits))
#            for j in range(0,8):
#                if (8*(i-2)+1+j) >= 255:    # Guard against incorrect configuration of too many flags.
#                    break   
#                self.flags.append(ComfortFLFlagActivationReport("", 8*(i-2)+1+j,(flagbits>>j) & 1))
#                logger.debug("Flags: %s %s", 8*(i-2)+1+j,(flagbits>>j) )
                 
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
            #end_flag = 8 + (8 * i)
            # Extract individual bit values and assign to flags
            flags = {}
            for j in range(1, 9):   # Flag 1 to 8 (Saved as 0 - 7)
                if (start_flag + j - 1) < 255:
                    flag_name = "flag" + str(start_flag + j - 1)
                    flags[flag_name] = int(segment[8 - j],2)
                    self.flags.append(ComfortFLFlagActivationReport("", int(start_flag + j - 1),int(segment[8 - j],2) & 1))
            
            #for flag_name, flag_value in flags.items():
            #    logger.debug (f"{flag_name}: {flag_value}")



        
        #logger.debug("len(data): %s", b)
        #logger.debug("data: %s", data)
#        for i in range(2,b+2):      
#            flagbits = int(data[2*i:2*i+2],16)
#            #print ("flagbits: %d" % (flagbits))
#            for j in range(0,8):
#                if (8*(i-2)+1+j) >= 255:    # Guard against incorrect configuration of too many flags.
#                    break   
#                self.flags.append(ComfortFLFlagActivationReport("", 8*(i-2)+1+j,(flagbits>>j) & 1))
#                logger.debug("Flags: %s %s", 8*(i-2)+1+j,(flagbits>>j) )

#mode = { 00=Off, 01=Away, 02=Night, 03=Day, 04=Vacation }
class ComfortM_SecurityModeReport(object):
    def __init__(self, data={}):
        self.mode = int(data[2:4],16)
        if self.mode == 0: self.modename = "Security Off"
        elif self.mode == 1: self.modename = "Away Mode"
        elif self.mode == 2: self.modename = "Night Mode"
        elif self.mode == 3: self.modename = "Day Mode"
        elif self.mode == 4: self.modename = "Vacation Mode"

#zone = 00 means system can be armed, no open zones
class ComfortERArmReadyNotReady(object):
    def __init__(self, data={}):
        self.zone = int(data[2:4],16)

class ComfortAMSystemAlarmReport(object):
    def __init__(self, data={}):
        self.alarm = int(data[2:4],16)
        self.triggered = True   #for comfort alarm state Alert, Trouble, Alarm
        self.parameter = int(data[4:6],16)
        low_battery = ['','Slave 1','Slave 2','Slave 3','Slave 4','Slave 5']
        if self.alarm == 0: self.message = "Intruder, Zone "+str(self.parameter)
        elif self.alarm == 1: self.message = "Zone "+str(self.parameter)+" Trouble"
        elif self.alarm == 2: self.message = "Low Battery - "+('Main' if self.parameter == 1 else low_battery[(self.parameter - 32)])
        elif self.alarm == 3: self.message = "Power Failure"
        elif self.alarm == 4: self.message = "Phone Trouble"
        elif self.alarm == 5: self.message = "Duress"
        elif self.alarm == 6: self.message = "Arm Failure"
        elif self.alarm == 8: self.message = "Disarm"; self.triggered = False
        elif self.alarm == 9: self.message = "Arm"; self.triggered = False
        elif self.alarm == 10: self.message = "Tamper"
        elif self.alarm == 12: self.message = "Entry Warning, Zone "+str(self.parameter); self.triggered = False
        elif self.alarm == 13: self.message = "Alarm Abort"; self.triggered = False
        elif self.alarm == 14: self.message = "Siren Tamper"
        elif self.alarm == 15: self.message = "Bypass, Zone "+str(self.parameter); self.triggered = False
        elif self.alarm == 17: self.message = "Dial Test"; self.triggered = False
        elif self.alarm == 19: self.message = "Entry Alert, Zone "+str(self.parameter); self.triggered = False
        elif self.alarm == 20: self.message = "Fire"
        elif self.alarm == 21: self.message = "Panic"
        elif self.alarm == 22: self.message = "GSM Trouble"
        elif self.alarm == 23: self.message = "New Message"; self.triggered = False
        elif self.alarm == 24: self.message = "Doorbell"; self.triggered = False
        elif self.alarm == 25: self.message = "Comms Failure RS485"
        elif self.alarm == 26: self.message = "Signin Tamper"

class ComfortEXEntryExitDelayStarted(object):
    def __init__(self, data={}):
        self.type = int(data[2:4],16)
        self.delay = int(data[4:6],16)

class Comfort2(mqtt.Client):

    global FIRST_LOGIN

    def init(self, mqtt_ip, mqtt_port, mqtt_username, mqtt_password, comfort_ip, comfort_port, comfort_pincode):
        self.mqtt_ip = mqtt_ip
        self.mqtt_port = mqtt_port
        self.comfort_ip = comfort_ip
        self.comfort_port = comfort_port
        self.comfort_pincode = comfort_pincode
        self.connected = False
        self.username_pw_set(mqtt_username, mqtt_password)

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc, properties):
        #print("Broker Connected with result code "+str(rc))
        #print("rc: %s", str(rc))
        if rc == 'Success':
            #logger.info('MQTT Broker %s (%s)', mqtt_strings[rc], str(rc))
            logger.info('MQTT Broker %s', str(rc))

            # You need to subscribe to your own topics to enable publish messages activating Comfort entities.
            self.subscribe(ALARMCOMMANDTOPIC)
            #logger.debug('ALARMNUMBEROFOUTPUTS: %s', str(ALARMNUMBEROFOUTPUTS))
            for i in range(1, ALARMNUMBEROFOUTPUTS + 1):
                self.subscribe(ALARMOUTPUTCOMMANDTOPIC % i)
                #logger.debug('ALARMOUTPUTCOMMANDTOPIC %s', str(ALARMOUTPUTCOMMANDTOPIC % i))
          
            for i in ALARMVIRTUALINPUTRANGE: #for virtual inputs #inputs+1 to 96
                #logger.debug('ALARMINPUTCOMMANDTOPIC %s', str(ALARMINPUTCOMMANDTOPIC % i))
                self.subscribe(ALARMINPUTCOMMANDTOPIC % i)
            
            for i in ALARMRIOINPUTRANGE: #for inputs 129 to Max Value
                #logger.debug('ALARMRIOINPUTCOMMANDTOPIC %s', str(ALARMRIOINPUTCOMMANDTOPIC % i))
                self.subscribe(ALARMRIOINPUTCOMMANDTOPIC % i)
            for i in ALARMRIOOUTPUTRANGE: #for outputs 129 to Max Value
                #logger.debug('ALARMRIOOUTPUTCOMMANDTOPIC %s', str(ALARMRIOOUTPUTCOMMANDTOPIC % i))
                self.subscribe(ALARMRIOOUTPUTCOMMANDTOPIC % i)
                
            for i in range(1, ALARMNUMBEROFFLAGS + 1):
                if i >= 255:
                    break
                #logger.debug('ALARMFLAGCOMMANDTOPIC %s', str(ALARMFLAGCOMMANDTOPIC % i))
                self.subscribe(ALARMFLAGCOMMANDTOPIC % i)
                
                ## Sensors ##
            for i in range(0, ALARMNUMBEROFSENSORS):
                #logger.debug('ALARMSENSORCOMMANDTOPIC %s', str(ALARMSENSORCOMMANDTOPIC % i))
                self.subscribe(ALARMSENSORCOMMANDTOPIC % i)

            for i in range(0, ALARMNUMBEROFCOUNTERS + 1):
                self.subscribe(ALARMCOUNTERCOMMANDTOPIC % i)  


            #for i in range(1, ALARMNUMBEROFRESPONSES + 1):
            #    self.subscribe(ALARMRESPONSECOMMANDTOPIC % i)
                

          
           
            
            if FIRST_LOGIN == 0:
                self.readcurrentstate()
            
        else:
            logger.error('MQTT Broker %s', str(rc))

    def on_disconnect(self, client, userdata, flags, rc, properties):  #client, userdata, flags, reason_code, properties
        if rc == 0:
            logger.info('MQTT Broker %s', str(rc))
        else:
            logger.error('MQTT Broker %s', str(rc))
            #logger.error('RC: (%s)', str(rc))

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg = 0):
        #logger.debug("on_message")
        msgstr = msg.payload.decode()
        #logger.debug(msg.topic+" "+msgstr)
        if msg.topic == ALARMCOMMANDTOPIC:      ## Revised Names used !!!! ## Also Check MQTT SET not working
            #logger.debug(msg.topic+" "+msgstr)
            if self.connected:
                if msgstr == "ARM_HOME":
                    self.comfortsock.sendall(("\x03m!03"+self.comfort_pincode+"\r").encode()) #arm to 03 day mode
                elif msgstr == "ARM_NIGHT":
                    self.comfortsock.sendall(("\x03m!02"+self.comfort_pincode+"\r").encode()) #arm to 02 night mode
                elif msgstr == "ARM_AWAY":
                    self.comfortsock.sendall(("\x03m!01"+self.comfort_pincode+"\r").encode()) #arm to 01 away mode
                elif msgstr == "DISARM":
                    self.comfortsock.sendall(("\x03m!00"+self.comfort_pincode+"\r").encode()) #arm to 00 disarm mode
        elif msg.topic.startswith(DOMAIN+"/output") and msg.topic.endswith("/set"):
            #logger.debug("msgstr: %s",msgstr )
            output = int(msg.topic.split("/")[1][6:])
            state = int(msgstr)
            if self.connected:
                self.comfortsock.sendall(("\x03O!%02X%02X\r" % (output, state)).encode())
        elif msg.topic.startswith(DOMAIN+"/response") and msg.topic.endswith("/set"):
            response = int(msg.topic.split("/")[1][8:])
            if self.connected:
                self.comfortsock.sendall(("\x03R!%02X\r" % response).encode())
        elif msg.topic.startswith(DOMAIN+"/input") and msg.topic.endswith("/set"):
            virtualinput = int(msg.topic.split("/")[1][5:])
            state = int(msgstr)
            if self.connected:
                self.comfortsock.sendall(("\x03I!%02X%02X\r" % (virtualinput, state)).encode())
                #logger.debug("VirtualInput: %s, State: %s",virtualinput,state )
        elif msg.topic.startswith(DOMAIN+"/flag") and msg.topic.endswith("/set"):
            flag = int(msg.topic.split("/")[1][4:])
            state = int(msgstr)
            if self.connected:
                self.comfortsock.sendall(("\x03F!%02X%02X\r" % (flag, state)).encode()) #was F!
                #logger.debug("Flag Set: %s, State: %s",flag,state )
        elif msg.topic.startswith(DOMAIN+"/counter") and msg.topic.endswith("/set"): # counter set
            counter = int(msg.topic.split("/")[1][7:])
            state = int(msgstr)
            if self.connected:
                self.comfortsock.sendall(("\x03C!%02X%s\r" % (counter, self.DecimalToSigned16(state))).encode()) # counter needs 16 bit signed number
        elif msg.topic.startswith(DOMAIN+"/sensor") and msg.topic.endswith("/set"): # sensor set
            #logger.debug("msg.topic: %s",msg.topic)
            sensor = int(msg.topic.split("/")[1][6:])
            state = int(msgstr)
            if self.connected:
                self.comfortsock.sendall(("\x03s!%02X%s\r" % (sensor, self.DecimalToSigned16(state))).encode()) # sensor needs 16 bit signed number
                #logger.debug("\x03s!%02X%s\r",sensor, self.DecimalToSigned16(state))

    def DecimalToSigned16(self,value):      # Returns Comfort corrected HEX string value from signed 16-bit decimal value.
        return ('{:04X}'.format((int((value & 0xff) * 0x100 + (value & 0xff00) / 0x100))) )
    
    #def HexToSigned16Decimal(self,value):        # Returns Signed Decimal value from HEX string EG. FFFF = -1
    #    #print("Value:", value)
    #    return -(int(value,16) & 0x8000) | (int(value,16) & 0x7fff)
    

    def HexToSigned16Decimal(self,value):        # Returns Signed Decimal value from HEX string EG. FFFF = -1
        logger.debug("690-HexToSigned16Decimal[value]: %s",value)
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
        #logger.debug("client: " + str(client))
        #logger.debug("mid: " + str(mid))
        #logger.debug("obj: " + str(obj))
        pass

    def on_subscribe(self, client, userdata, mid, reason_codes, properties):
        #print("subscribed "+str(userdata))
        for sub_result in reason_codes:
            if sub_result == 1:
                logger.debug("QoS == 1")
            if sub_result >= 128:
                logger.debug("Error processing subscribe")
        #pass

    def on_log(self, client, userdata, level, buf):
        #print("log: ",buf)
        pass

    def entryexit_timer(self):
        #print("timer: "+str(self.entryexitdelay))
        self.publish(ALARMTIMERTOPIC, self.entryexitdelay,qos=0,retain=True)
        self.entryexitdelay -= 1
        if self.entryexitdelay >= 0:
            threading.Timer(1, self.entryexit_timer).start()

    def readlines(self, recv_buffer=BUFFER_SIZE, delim='\r'):

        global FIRST_LOGIN

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
                    #sleep(1)
                    #print ('recv timed out, retry later')
                    self.comfortsock.sendall("\x03cc00\r".encode()) #echo command for keepalive
                    continue
                else:
                    print (e)
    #sys.exit(1)
            except socket.error as e:
                # Something else happened, handle error, exit, etc.
                logger.debug("Something else happened %s", e)
                FIRST_LOGIN = 1
                raise
                #sys.exit(1)
            else:
                if len(data) == 0:
                    #logger.info('Orderly disconnect on Comfort end')
                    FIRST_LOGIN = 1
                #sys.exit(0)
                else:
                    # got a message do something :)
                    buffer += data

                    while buffer.find(delim) != -1:
                        line, buffer = buffer.split('\r', 1)
                        yield line
        return

    def login(self):
        self.comfortsock.sendall(("\x03LI"+self.comfort_pincode+"\r").encode())

    def readcurrentstate(self):
        if self.connected == True:
            #get Security Mode
            self.comfortsock.sendall("\x03M?\r".encode())
            #get all zone input states
            self.comfortsock.sendall("\x03Z?\r".encode())
            #get all SCS/RIO input states
            self.comfortsock.sendall("\x03z?\r".encode())
            #get all output states
            self.comfortsock.sendall("\x03Y?\r".encode())
            #get all RIO output states
            self.comfortsock.sendall("\x03y?\r".encode())       # Request/Report all RIO Outputs
            #get all flag states
            self.comfortsock.sendall("\x03f?00\r".encode())

            #get all sensor values. 0 - 31
            #get all sensor states
            self.comfortsock.sendall("\x03r?010010\r".encode())
            self.comfortsock.sendall("\x03r?011010\r".encode())

          #get all counter values
            for i in range(0, int((ALARMNUMBEROFCOUNTERS+1) / 16)):          # Counters 0 to 254 Using 256/16 = 16 iterations
                #query = f"{i:#0{3}X}"[2:]+"0"
                #self.comfortsock.sendall("\x03r?00%02X10\r".encode() % (i))
                #logger.debug("self.comfortsock.sendall(r?00%X010.encode()" % (i))
                self.comfortsock.sendall("\x03r?00%X010\r".encode() % (i))
                time.sleep(0.05)

            
            self.publish(ALARMAVAILABLETOPIC, 1,qos=0,retain=True)
            self.publish(ALARMLWTTOPIC, 'Online',qos=0,retain=True)
            self.publish(ALARMMESSAGETOPIC, "",qos=0,retain=True)

    def setdatetime(self):
        if self.connected == True:  #set current date and time if COMFORT_TIME Flag is set to True
            #logger.debug('COMFORT_TIME=%s', COMFORT_TIME)
            if COMFORT_TIME == 'True':
                logger.info('Setting Comfort Date/Time')
                now = datetime.now()
                self.comfortsock.sendall(("\x03DT%02d%02d%02d%02d%02d%02d\r" % (now.year, now.month, now.day, now.hour, now.minute, now.second)).encode())

    def check_string(self, s):
        pattern = r'^\x03[a-zA-Z]{1}'
        if re.match(pattern, s):
            return True
        else:
            return False

    def run(self):

        global FIRST_LOGIN         # Used to track if Addon started up or not.
#        FIRST_LOGIN = 0

        self.connect_async(self.mqtt_ip, self.mqtt_port, 60)
        self.loop_start()
        self.publish(ALARMAVAILABLETOPIC, 0,qos=0,retain=True)
        self.will_set(ALARMLWTTOPIC, payload="Offline", qos=0, retain=True)
        logging.debug("Self.Connected: %s", str(self.connected))
        try:
            while True:
                try:
                    self.comfortsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    #print("Connecting to "+self.comfort_ip+" "+str(self.comfort_port))
                    logger.info('Connecting to Comfort (%s) on port %s', self.comfort_ip, str(self.comfort_port) )
                    self.comfortsock.connect((self.comfort_ip, self.comfort_port))
                    self.comfortsock.settimeout(TIMEOUT.seconds)
                    self.login()

                    for line in self.readlines():
                        if line[1:] != "cc00":
                            logger.debug(line[1:])  	# Print all responses only in DEBUG mode. Print all received Comfort commands.
                        if self.check_string(line[:3]):  #"\x03":   #check for valid prefix.
                            if line[1:3] == "LU":
                                luMsg = ComfortLUUserLoggedIn(line[1:])
                                if luMsg.user != 0:
                                    logger.info('Comfort Login Ok - User %s', (luMsg.user if luMsg.user != 254 else 'Engineer'))
                                    #self.connected = True

                                    logger.debug("Starting 3s delay...")
                                    delay = timedelta(seconds=3)
                                    endtime = datetime.now() + delay
                                    while datetime.now() < endtime:
                                       pass
                                    logger.debug("...Finished")

                                    self.connected = True

                                    #client.publish(ALARMSTATETOPIC, "disarmed")
                                    self.publish(ALARMCOMMANDTOPIC, "comm test",qos=0,retain=True)
                                    self.setdatetime()      # Set Date/Time if Flag is set
                                    if FIRST_LOGIN == 1:
                                        self.readcurrentstate()
                                        FIRST_LOGIN = 0
                            elif line[1:5] == "PS00":     # Set Date/Time once a day on receipt of PS command. Usually midnight or any time the system is armed.
                                #logger.debug('In the PS00 section')
                                self.setdatetime()          # Set Date/Time if Flag is set at 00:00 every day.
                            elif line[1:3] == "IP":
                                ipMsg = ComfortIPInputActivationReport(line[1:])
                                #print("input %d state %d" % (ipMsg.input, ipMsg.state))
                                self.publish(ALARMINPUTTOPIC % ipMsg.input, ipMsg.state,qos=0,retain=True)
                            elif line[1:3] == "CT":
                                ipMsgCT = ComfortCTCounterActivationReport(line[1:])
                                #print("counter %d state %d" % (ipMsgCT.counter, ipMsgCT.state))
                                self.publish(ALARMCOUNTERINPUTRANGE % ipMsgCT.counter, ipMsgCT.state,qos=0,retain=True)
                            elif line[1:3] == "s?":
                                ipMsgSQ = ComfortCTCounterActivationReport(line[1:])
                                #logger.debug("sensor %s state %s" % (ipMsgSR.counter, ipMsgSR.state))
                                self.publish(ALARMSENSORTOPIC % ipMsgSQ.counter, ipMsgSQ.state)
                            elif line[1:3] == "sr":
                                ipMsgSR = ComfortCTCounterActivationReport(line[1:])
                                #logger.debug("sensor %d state %d" % (ipMsgSR.counter, self.HexToSigned16Decimal(ipMsgSR.state)))
                                #logger.debug("state %s" % ipMsgSR.state)
                                #self.publish(ALARMSENSORTOPIC % ipMsgSR.counter, self.HexToSigned16Decimal(ipMsgSR.state))
                                self.publish(ALARMSENSORTOPIC % ipMsgSR.counter, ipMsgSR.state)
                            elif line[1:3] == "TR":
                                ipMsgTR = ComfortCTCounterActivationReport(line[1:])
                                #logger.debug("timer %d value(s) %d" % (ipMsgTR.counter, ipMsgTR.state))
                                #logger.debug("state %s" % ipMsgSR.state)
                                #self.publish(ALARMSENSORTOPIC % ipMsgSR.counter, self.HexToSigned16Decimal(ipMsgSR.state))
                                self.publish(ALARMTIMERTOPIC % ipMsgTR.counter, ipMsgTR.state)
                            elif line[1:3] == "Z?":
                                zMsg = ComfortZ_ReportAllZones(line[1:])
                                for ipMsgZ in zMsg.inputs:
                                    #print("input %d state %d" % (ipMsgZ.input, ipMsgZ.state))
                                    self.publish(ALARMINPUTTOPIC % ipMsgZ.input, ipMsgZ.state)
                            elif line[1:3] == "z?":
                                zMsg = Comfort_Z_ReportAllZones(line[1:])
                                for ipMsgZ in zMsg.inputs:
                                    #logger.debug("RIO input %d state %d" % (ipMsgZ.input, ipMsgZ.state))
                                    self.publish(ALARMINPUTTOPIC % ipMsgZ.input, ipMsgZ.state)
                            elif line[1:3] == "M?" or line[1:3] == "MD":
                                mMsg = ComfortM_SecurityModeReport(line[1:])
                                #logging.debug("Alarm Mode %s", mMsg.modename)
                                self.publish(ALARMSTATETOPIC, mMsg.modename,qos=0,retain=True)
                                self.entryexitdelay = 0    #zero out the countdown timer
                            #elif line[1:3] == "S?":
                            #    mMsg = ComfortM_SecurityModeReport(line[1:])
                            #    #logging.debug("Alarm Mode %s", mMsg.modename)
                            #    self.publish(ALARMSTATETOPIC, mMsg.modename,qos=0,retain=True)
                            #    self.entryexitdelay = 0    #zero out the countdown timer
                            elif line[1:3] == "ER":
                                erMsg = ComfortERArmReadyNotReady(line[1:])
                                if not erMsg.zone == 0:
                                    #print("zone not ready: "+str(erMsg.zone))
                                    self.comfortsock.sendall("\x03KD1A\r".encode()) #force arm
                            elif line[1:3] == "AM":
                                amMsg = ComfortAMSystemAlarmReport(line[1:])
                                self.publish(ALARMMESSAGETOPIC, amMsg.message,qos=0,retain=True)
                                if amMsg.triggered:
                                    self.publish(ALARMSTATETOPIC, "Triggered",qos=0,retain=True)
                            elif line[1:3] == "EX":
                                exMsg = ComfortEXEntryExitDelayStarted(line[1:])
                                self.entryexitdelay = exMsg.delay
                                self.entryexit_timer()
                                self.publish(ALARMSTATETOPIC, "Pending",qos=0,retain=True)
                            elif line[1:3] == "RP":
                                self.publish(ALARMMESSAGETOPIC, "Phone Ring",qos=0,retain=True)
                            elif line[1:3] == "DB":
                                self.publish(ALARMDOORBELLTOPIC, 1 if line[1:] != "DBFF" else 0,qos=0,retain=True)
                            elif line[1:3] == "OP":
                                ipMsg = ComfortOPOutputActivationReport(line[1:])
                                #print("output %d state %d" % (ipMsg.output, ipMsg.state))
                                self.publish(ALARMOUTPUTTOPIC % ipMsg.output, ipMsg.state,qos=0,retain=True)
                            elif line[1:3] == "Y?":
                                yMsg = ComfortY_ReportAllOutputs(line[1:])
                                for opMsgY in yMsg.outputs:
                                    #print("output %d state %d" % (opMsgY.output, opMsgY.state))
                                    self.publish(ALARMOUTPUTTOPIC % opMsgY.output, opMsgY.state,qos=0,retain=True)
                            elif line[1:3] == "y?":
                                yMsg = Comfort_Y_ReportAllOutputs(line[1:])
                                for opMsgY in yMsg.outputs:
                                    #print("RIO output %d state %d" % (opMsgY.output, opMsgY.state))
                                    self.publish(ALARMOUTPUTTOPIC % opMsgY.output, opMsgY.state)
                            elif line[1:5] == "r?00":
                                cMsg = Comfort_R_ReportAllSensors(line[1:])
                                for cMsgr in cMsg.counters:
                                    #logger.debug("counter %s state %s" % (cMsgr.counter, cMsgr.state))
                                    self.publish(ALARMCOUNTERINPUTRANGE % cMsgr.counter, cMsgr.state,qos=0,retain=True)
                            elif line[1:5] == "r?01":
                                sMsg = Comfort_R_ReportAllSensors(line[1:])
                                for sMsgr in sMsg.sensors:
                                    #print("sensor %d state %d" % (sMsgr.sensor, sMsgr.value))
                                    self.publish(ALARMSENSORTOPIC % sMsgr.sensor, sMsgr.value,qos=0,retain=True)
                            elif (line[1:3] == "f?") and (len(line) == 69):
                                fMsg = Comfortf_ReportAllFlags(line[1:])
                                for fMsgf in fMsg.flags:
                                    #print("flag %d state %d" % (fMsgf.flag, fMsgf.state))
                                    self.publish(ALARMFLAGTOPIC % fMsgf.flag, fMsgf.state,qos=0,retain=True)
                            elif line[1:3] == "FL":
                                flMsg = ComfortFLFlagActivationReport(line[1:])
                                #print("flag %d state %d" % (flMsg.flag, flMsg.state))
                                self.publish(ALARMFLAGTOPIC % flMsg.flag, flMsg.state,qos=0,retain=True)
                            elif line[1:3] == "RS":
                                #on rare occassions comfort ucm might get reset (RS11), our session is no longer valid, need to relogin
                                logger.warning('Reset detected')
                                self.login()
                except socket.error as v:
                    ##errorcode = v[0]
                    logger.error('Comfort Socket Error %s', str(v))
                    ##raise
                logger.error('Lost connection to Comfort, reconnecting...')
                self.publish(ALARMAVAILABLETOPIC, 0,qos=0,retain=True)
                self.publish(ALARMLWTTOPIC, 'Offline',qos=0,retain=True)
                time.sleep(RETRY.seconds)
        finally:
            infot = self.publish(ALARMAVAILABLETOPIC, 0,qos=0,retain=True)
            infot = self.publish(ALARMLWTTOPIC, 'Offline',qos=0,retain=True)
            infot.wait_for_publish()

#print("MQTTBROKERIP: %s " % MQTTBROKERIP)
#print("MQTTBROKERPORT: %s " % MQTTBROKERPORT)
#print("MQTTUSERNAME: %s " % MQTTUSERNAME)
#print("MQTTPASSWORD: %s " % MQTTPASSWORD)
#print("COMFORTIP: %s " % COMFORTIP)
#print("COMFORTPORT: %s " % COMFORTPORT)
#print("PINCODE: %s " % PINCODE)
#print("COMFORT_INPUTS: %s " % COMFORT_INPUTS)
#print("COMFORT_OUTPUTS: %s " % COMFORT_OUTPUTS)
#print("COMFORT_RESPONSES: %s " % COMFORT_RESPONSES)
#print("COMFORT_FLAGS: %s " % COMFORT_FLAGS)
#print("COMFORT_COUNTERS: %s " % COMFORT_COUNTERS)

mqttc = Comfort2(mqtt.CallbackAPIVersion.VERSION2, DOMAIN)
#logging.debug("1:%s",str(mqttc))
mqttc.init(MQTTBROKERIP, MQTTBROKERPORT, MQTTUSERNAME, MQTTPASSWORD, COMFORTIP, COMFORTPORT, PINCODE)
#logging.debug("2:%s",str(mqttc))
mqttc.run()
