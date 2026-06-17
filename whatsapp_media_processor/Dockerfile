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
    ffmpeg \
    go \
    git \
    bash \
    ca-certificates

RUN pip3 install \
    flask \
    openai \
    --break-system-packages

ENV GOROOT=/usr/lib/go
ENV GOPATH=/go
ENV PATH=/go/bin:$PATH

RUN mkdir -p ${GOPATH}/src ${GOPATH}/bin

RUN go install github.com/ddz/whatsapp-media-decrypt@latest

WORKDIR /data

COPY server.py /
COPY run.sh /

RUN chmod a+x /run.sh
RUN chmod a+x /server.py

CMD ["/run.sh"]
