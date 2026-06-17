FROM ghcr.io/home-assistant/base:latest

ARG BUILD_VERSION=dev
ARG BUILD_ARCH=amd64

LABEL \
    io.hass.version="${BUILD_VERSION}" \
    io.hass.type="app" \
    io.hass.arch="${BUILD_ARCH}"

RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-pillow \
    py3-cryptography \
    ffmpeg \
    bash \
    ca-certificates

RUN pip3 install \
    flask \
    openai \
    --break-system-packages

WORKDIR /data

COPY server.py /
COPY run.sh /

RUN chmod a+x /run.sh
RUN chmod a+x /server.py

CMD ["/run.sh"]
