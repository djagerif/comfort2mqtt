ARG BUILD_FROM
FROM $BUILD_FROM

# Install most Python deps here, because that way we don't need to include build tools in the
# final image.

RUN apk update --no-cache && apk upgrade --no-cache
RUN pip install --no-cache-dir --upgrade pip
RUN pip install paho-mqtt pyopenssl requests defusedxml
RUN pip install websocket-client

# Copy root filesystem
COPY rootfs /

RUN chmod 755 /etc/services.d/comfort2mqtt/run
RUN chmod 755 /etc/services.d/comfort2mqtt/finish
