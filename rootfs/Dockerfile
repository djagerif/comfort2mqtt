ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk update --no-cache && apk upgrade --no-cache
RUN pip install --no-cache-dir --upgrade pip
RUN pip install paho-mqtt

# Copy root filesystem
COPY rootfs /

# Copy data for add-on
#COPY run.sh /
#COPY comfort2.py /
#
#RUN chmod a+x /run.sh
#RUN chmod a+x /comfort2.py
#
#CMD [ "/run.sh" ]
