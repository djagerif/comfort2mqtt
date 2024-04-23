#!/usr/bin/with-contenv bashio

# Import the add-on configuration options as environment variables

MQTT_USER=$(bashio::config 'mqtt_user')
MQTT_PASSWORD=$(bashio::config 'mqtt_password')
MQTT_SERVER=$(bashio::config 'mqtt_broker_address')
MQTT_PORT=$(bashio::config 'mqtt_broker_port')
COMFORT_ADDRESS=$(bashio::config 'comfort_address')
COMFORT_PORT=$(bashio::config 'comfort_port')
COMFORT_LOGIN_ID=$(bashio::config 'comfort_login_id')
#MQTT_CA_CERT_PATH=$(bashio::config 'broker_ca')                #  For future development !!!
#MQTT_CLIENT_CERT_PATH=$(bashio::config 'broker_client_cert')   #  For future development !!!
#MQTT_CLIENT_KEY_PATH=$(bashio::config 'broker_client_key')     #  For future development !!!
MQTT_LOG_LEVEL=$(bashio::config 'log_verbosity')
COMFORT_INPUTS=$(bashio::config 'alarm_inputs')
COMFORT_OUTPUTS=$(bashio::config 'alarm_outputs')
COMFORT_RIO_INPUTS=$(bashio::config 'alarm_rio_inputs')
COMFORT_RIO_OUTPUTS=$(bashio::config 'alarm_rio_outputs')
COMFORT_RESPONSES=$(bashio::config 'alarm_responses')
COMFORT_FLAGS=$(bashio::config 'alarm_flags')
COMFORT_COUNTERS=$(bashio::config 'alarm_counters')
COMFORT_TIME=$(bashio::config 'comfort_time')

# Arguments that are always required.
COMFORT_ARGS="--broker-address ${MQTT_SERVER:?unset}"

# Simple arguments
if [ "${MQTT_PORT}" != "null" ]; then
   COMFORT_ARGS="${COMFORT_ARGS} --broker-port ${MQTT_PORT}"
fi

if [ "${MQTT_USER}" != "null" ]; then
    COMFORT_ARGS="${COMFORT_ARGS} --broker-username ${MQTT_USER}"
fi

if [ "${MQTT_PASSWORD}" != "null" ]; then
    COMFORT_ARGS="${COMFORT_ARGS} --broker-password ${MQTT_PASSWORD}"
fi

if [ "${COMFORT_ADDRESS}" != "null" ]; then
    COMFORT_ARGS="${COMFORT_ARGS} --comfort-address ${COMFORT_ADDRESS}"
fi

if [ "${COMFORT_PORT}" != "null" ]; then
    COMFORT_ARGS="${COMFORT_ARGS} --comfort-port ${COMFORT_PORT}"
fi

if [ "${COMFORT_LOGIN_ID}" != "null" ]; then
    COMFORT_ARGS="${COMFORT_ARGS} --comfort-login-id ${COMFORT_LOGIN_ID}"
fi

if [ "${COMFORT_INPUTS}" != "null" ]; then
    COMFORT_ARGS="${COMFORT_ARGS} --alarm-inputs ${COMFORT_INPUTS}"
fi

if [ "${COMFORT_OUTPUTS}" != "null" ]; then
    COMFORT_ARGS="${COMFORT_ARGS} --alarm-outputs ${COMFORT_OUTPUTS}"
fi

if [ "${COMFORT_RIO_INPUTS}" != "null" ]; then
    COMFORT_ARGS="${COMFORT_ARGS} --alarm-rio-inputs ${COMFORT_RIO_INPUTS}"
fi

if [ "${COMFORT_RIO_OUTPUTS}" != "null" ]; then
    COMFORT_ARGS="${COMFORT_ARGS} --alarm-rio-outputs ${COMFORT_RIO_OUTPUTS}"
fi

if [ "${COMFORT_RESPONSES}" != "null" ]; then
    COMFORT_ARGS="${COMFORT_ARGS} --alarm-responses ${COMFORT_RESPONSES}"
fi

if [ "${COMFORT_FLAGS}" != "null" ]; then
    COMFORT_ARGS="${COMFORT_ARGS} --alarm-flags ${COMFORT_FLAGS}"
fi

if [ "${COMFORT_COUNTERS}" != "null" ]; then
    COMFORT_ARGS="${COMFORT_ARGS} --alarm-counters ${COMFORT_COUNTERS}"
fi

if [ "${COMFORT_TIME}" != "null" ]; then
    COMFORT_ARGS="${COMFORT_ARGS} --comfort-time ${COMFORT_TIME}"
fi

if [ "${MQTT_LOG_LEVEL}" != "null" ]; then
      COMFORT_ARGS="$COMFORT_ARGS --verbosity $MQTT_LOG_LEVEL"
fi

# "Running comfort2mqtt with flags: ${COMFORT_ARGS}"
python3 comfort2.py $COMFORT_ARGS

