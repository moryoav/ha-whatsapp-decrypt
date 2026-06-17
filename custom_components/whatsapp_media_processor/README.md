# WhatsApp Media Processor Integration

Home Assistant custom integration for the WhatsApp Media Processor add-on.

The integration exposes add-on media processing as Home Assistant actions and discovers the running add-on through Supervisor discovery.

## Installation

1. Install and start the **WhatsApp Media Processor** add-on from this repository.
2. Copy `custom_components/whatsapp_media_processor` into your Home Assistant `/config/custom_components/` directory, or install this repository as a HACS custom integration.
3. Restart Home Assistant.
4. Go to **Settings** > **Devices & services** > **Add integration**.
5. Add **WhatsApp Media Processor**.

The setup flow checks the add-on `/health` endpoint before saving the config entry.

## Actions

The integration exposes these actions:

- `whatsapp_media_processor.process_audio`
- `whatsapp_media_processor.process_document`
- `whatsapp_media_processor.process_image`
- `whatsapp_media_processor.process_video`

All actions accept a `timeout` field. They support optional response data through `response_variable`.

## Examples

### Audio

```yaml
action: whatsapp_media_processor.process_audio
data:
  code: "{{ code }}"
  url: "{{ url }}"
response_variable: whatsapp_audio
```

### Document

```yaml
action: whatsapp_media_processor.process_document
data:
  code: "{{ code }}"
  url: "{{ url }}"
  filename: "{{ filename }}"
response_variable: whatsapp_document
```

Set `save_dir` to override the configured document save folder for a single call. Document responses include `file`/`path` for the saved document and `text`/`combined_text` with labeled Tesseract/OpenAI sections. Use `tesseract_text` or `openai_output_text` when an automation needs one OCR source specifically.

### Image

```yaml
action: whatsapp_media_processor.process_image
data:
  code: "{{ code }}"
  url: "{{ url }}"
  text: "{{ text }}"
response_variable: whatsapp_image
```

Image responses include `text` and `combined_text` with labeled Tesseract/OpenAI sections. Use `tesseract_text` or `openai_output_text` when an automation needs one OCR source specifically.

For stickers, call `process_image` with `media_type: sticker`.

### Video

```yaml
action: whatsapp_media_processor.process_video
data:
  user_id: "{{ userId }}"
  ffmpeg: "{{ ffmpeg }}"
  timeout: 180
response_variable: whatsapp_video
```

See the repository README for examples using `new_whatsapp_message` events from the WhatsApp integration in `moryoav/ha-addons`.
