FROM ghcr.io/home-assistant/base-python:latest

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy root filesystem
COPY rootfs /

RUN chmod 755 /etc/services.d/comfort2mqtt/run
RUN chmod 755 /etc/services.d/comfort2mqtt/finish
