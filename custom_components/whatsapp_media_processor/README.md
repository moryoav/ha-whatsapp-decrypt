# WhatsApp Media Processor Integration

This custom integration replaces `rest_command` wrappers with Home Assistant service actions for the WhatsApp Media Processor add-on.

## Installation

1. Install and start the **WhatsApp Media Processor** add-on from this repository.
2. Copy `custom_components/whatsapp_media_processor` into your Home Assistant `/config/custom_components/` directory, or install this repository as a HACS custom integration.
3. Restart Home Assistant.
4. Go to **Settings** > **Devices & services** > **Add integration**.
5. Add **WhatsApp Media Processor** and enter the add-on base URL, for example:

   ```text
   http://192.168.1.229:9000
   ```

The setup flow checks the add-on `/health` endpoint before saving the config entry.

## Actions

The integration exposes these actions:

- `whatsapp_media_processor.process_audio`
- `whatsapp_media_processor.process_document`
- `whatsapp_media_processor.process_image`
- `whatsapp_media_processor.process_video`

All actions accept a `timeout` field. They support optional response data through `response_variable`.

## Examples

```yaml
action: whatsapp_media_processor.process_audio
data:
  code: "{{ code }}"
  url: "{{ url }}"
response_variable: whatsapp_audio
```

```yaml
action: whatsapp_media_processor.process_document
data:
  code: "{{ code }}"
  url: "{{ url }}"
  filename: "{{ filename }}"
response_variable: whatsapp_document
```

```yaml
action: whatsapp_media_processor.process_image
data:
  code: "{{ code }}"
  url: "{{ url }}"
  text: "{{ text }}"
response_variable: whatsapp_image
```

```yaml
action: whatsapp_media_processor.process_video
data:
  user_id: "{{ userId }}"
  ffmpeg: "{{ ffmpeg }}"
  timeout: 180
response_variable: whatsapp_video
```

For stickers, call `process_image` with `media_type: sticker`.
