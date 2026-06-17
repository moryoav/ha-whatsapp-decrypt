# WhatsApp Media Processor for Home Assistant

[![HACS Custom][hacs-badge]][hacs-url]
[![Home Assistant][ha-badge]][ha-url]
[![Release][release-badge]][release-url]
[![Add-on][addon-badge]][addon-url]
[![License: MIT][license-badge]][license-url]

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=flat-square
[hacs-url]: https://www.hacs.xyz/
[ha-badge]: https://img.shields.io/badge/Home%20Assistant-2024.12%2B-18BCF2.svg?style=flat-square
[ha-url]: https://www.home-assistant.io/
[release-badge]: https://img.shields.io/github/v/release/moryoav/ha-whatsapp-decrypt?style=flat-square
[release-url]: https://github.com/moryoav/ha-whatsapp-decrypt/releases/latest
[addon-badge]: https://img.shields.io/badge/Home%20Assistant-add--on-41BDF5.svg?style=flat-square
[addon-url]: https://github.com/moryoav/ha-whatsapp-decrypt/tree/main/whatsapp_media_processor
[license-badge]: https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square
[license-url]: https://github.com/moryoav/ha-whatsapp-decrypt/blob/main/LICENSE

Home Assistant add-on and companion custom integration for decrypting and processing WhatsApp media from automations.

The add-on handles the media work. The integration exposes Home Assistant actions that call the add-on through Supervisor discovery, so automations can process WhatsApp media without configuring an IP address or port.

This repository is designed to be used together with the WhatsApp integration in [moryoav/ha-addons](https://github.com/moryoav/ha-addons). That integration receives WhatsApp messages and emits `new_whatsapp_message` events. This add-on processes the encrypted media URLs and media keys from those events.

## What It Does

- Decrypts WhatsApp audio, documents, images, stickers, and prepared video-processing requests.
- Transcribes audio with the configured OpenAI audio model.
- Analyzes images and stickers with the OpenAI Responses API.
- Saves decrypted documents to the configured Paperless consume directory.
- Runs prepared `ffmpeg` commands for video processing workflows.
- Exposes Home Assistant actions through the `whatsapp_media_processor` integration.

## Easy Installation

### Add-on Repository

[![Add the WhatsApp Media Processor add-on repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmoryoav%2Fha-whatsapp-decrypt)

1. Add this repository to the Home Assistant add-on store.
2. Install **WhatsApp Media Processor**.
3. Set the add-on options, especially `openai_api_key`.
4. Start the add-on.

[![Open the WhatsApp Media Processor add-on](https://my.home-assistant.io/badges/supervisor_addon.svg)](https://my.home-assistant.io/redirect/supervisor_addon/?addon=da354dd6_whatsapp_media_processor&repository_url=https%3A%2F%2Fgithub.com%2Fmoryoav%2Fha-whatsapp-decrypt)

### Custom Integration

[![Open the WhatsApp Media Processor HACS repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=moryoav&repository=ha-whatsapp-decrypt&category=integration)

1. Add this repository to HACS as a custom integration repository.
2. Install **WhatsApp Media Processor** from HACS.
3. Restart Home Assistant.
4. Add the integration from **Settings** -> **Devices & services** -> **Add integration**.

[![Add the WhatsApp Media Processor integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=whatsapp_media_processor)

The integration finds the running add-on through Supervisor discovery and checks the add-on health endpoint during setup.

## Manual Installation

### Add-on

1. In Home Assistant, go to **Settings** -> **Add-ons** -> **Add-on Store**.
2. Open the three-dot menu and select **Repositories**.
3. Add this repository URL:

   ```text
   https://github.com/moryoav/ha-whatsapp-decrypt
   ```

4. Install and start **WhatsApp Media Processor**.

### Integration

1. Copy `custom_components/whatsapp_media_processor` to `/config/custom_components/whatsapp_media_processor`.
2. Restart Home Assistant.
3. Add **WhatsApp Media Processor** from **Settings** -> **Devices & services** -> **Add integration**.

## Add-on Options

| Option | Default | Description |
| --- | --- | --- |
| `openai_api_key` | empty | OpenAI API key used for audio transcription and image analysis. |
| `audio_model` | `whisper-1` | OpenAI audio transcription model. |
| `image_model` | `gpt-5.4-mini` | OpenAI image analysis model. |
| `image_max_output_tokens` | `12000` | Maximum generated output tokens for image analysis. |
| `paperless_consume_dir` | `/share/Paperless_ngx_consume` | Directory where decrypted documents are saved. |

## Actions

The integration exposes these Home Assistant actions:

| Action | Required data | Result |
| --- | --- | --- |
| `whatsapp_media_processor.process_audio` | `code`, `url` | Decrypts WhatsApp audio and returns transcript text. |
| `whatsapp_media_processor.process_document` | `code`, `url`, `filename` | Decrypts a document and saves it to `paperless_consume_dir`. |
| `whatsapp_media_processor.process_image` | `code`, `url`, `text` | Decrypts an image, sends it to OpenAI with the prompt/caption, and returns the analysis text. |
| `whatsapp_media_processor.process_video` | `ffmpeg` | Runs a base64-encoded `ffmpeg` command and returns output file metadata. |

All actions accept `timeout` in seconds. `process_image` also accepts `media_type: sticker` for WhatsApp stickers. `process_video` can also accept `user_id`.

Use `response_variable` when the automation needs the result.

## Using With moryoav/ha-addons WhatsApp

The WhatsApp integration from [moryoav/ha-addons](https://github.com/moryoav/ha-addons) emits `new_whatsapp_message` events. Media events include a `url` and `mediaKey` under the message type.

### Audio

```yaml
- alias: Audio message
  condition: template
  value_template: "{{ trigger.event.data.type == 'audioMessage' }}"
- action: whatsapp_media_processor.process_audio
  data:
    url: "{{ trigger.event.data.message.audioMessage.url }}"
    code: "{{ trigger.event.data.message.audioMessage.mediaKey }}"
  response_variable: whatsapp_msg
- variables:
    request_text: "{{ whatsapp_msg.text | default('', true) | string | trim }}"
```

### Document

Document messages can arrive as `documentMessage` or as `documentWithCaptionMessage`. Extract the inner document first, then pass the media URL, media key, and filename to the action.

```yaml
- variables:
    document_url: >-
      {% set msg = trigger.event.data.message | default({}, true) %}
      {% if trigger.event.data.type == 'documentWithCaptionMessage' %}
        {{ msg.get('documentWithCaptionMessage', {}).get('message', {}).get('documentMessage', {}).get('url', '') | string | trim }}
      {% else %}
        {{ msg.get('documentMessage', {}).get('url', '') | string | trim }}
      {% endif %}
    document_media_key: >-
      {% set msg = trigger.event.data.message | default({}, true) %}
      {% if trigger.event.data.type == 'documentWithCaptionMessage' %}
        {{ msg.get('documentWithCaptionMessage', {}).get('message', {}).get('documentMessage', {}).get('mediaKey', '') | string | trim }}
      {% else %}
        {{ msg.get('documentMessage', {}).get('mediaKey', '') | string | trim }}
      {% endif %}
    document_filename: >-
      {% set msg = trigger.event.data.message | default({}, true) %}
      {% if trigger.event.data.type == 'documentWithCaptionMessage' %}
        {% set doc = msg.get('documentWithCaptionMessage', {}).get('message', {}).get('documentMessage', {}) %}
      {% else %}
        {% set doc = msg.get('documentMessage', {}) %}
      {% endif %}
      {{ doc.get('fileName', doc.get('title', 'document.pdf')) | string | trim }}
- action: whatsapp_media_processor.process_document
  data:
    url: "{{ document_url }}"
    code: "{{ document_media_key }}"
    filename: "{{ document_filename }}"
  response_variable: whatsapp_msg
```

For production automations, validate that `document_url` and `document_media_key` are not empty before calling the action.

### Image

```yaml
- alias: Image message
  condition: template
  value_template: "{{ trigger.event.data.type == 'imageMessage' }}"
- action: whatsapp_media_processor.process_image
  data:
    url: "{{ trigger.event.data.message.imageMessage.url }}"
    code: "{{ trigger.event.data.message.imageMessage.mediaKey }}"
    text: "{{ trigger.event.data.message.imageMessage.caption | default('', true) }}"
  response_variable: whatsapp_msg
- variables:
    request_text: "{{ whatsapp_msg.text | default(whatsapp_msg.output_text | default('', true), true) | string | trim }}"
```

### Sticker

```yaml
- action: whatsapp_media_processor.process_image
  data:
    url: "{{ trigger.event.data.message.stickerMessage.url }}"
    code: "{{ trigger.event.data.message.stickerMessage.mediaKey }}"
    text: "Describe this sticker."
    media_type: sticker
  response_variable: whatsapp_msg
```

### Video

`process_video` is for workflows that already build a base64-encoded `ffmpeg` command:

```yaml
- action: whatsapp_media_processor.process_video
  data:
    user_id: "{{ user_id }}"
    ffmpeg: "{{ ffmpeg }}"
    timeout: 180
  response_variable: whatsapp_video
```

## Response Data

Typical response values:

- Audio: `text`
- Document: `message`, `file`
- Image and sticker: `text`, `output_text`, `choices`, and native OpenAI Responses API fields
- Video: `files`, `user`

## Notes

- This project needs Home Assistant with Supervisor because the integration discovers the add-on through the Supervisor API.
- The add-on API is internal to Home Assistant. Automations should call the integration actions.
- Keep media keys, encrypted media URLs, logs, and OpenAI keys out of public issues and screenshots.
