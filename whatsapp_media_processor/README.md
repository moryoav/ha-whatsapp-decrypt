# WhatsApp Media Processor

Home Assistant add-on that decrypts WhatsApp media and prepares it for automations through the companion `whatsapp_media_processor` integration.

## What It Handles

- Audio: decrypts WhatsApp audio and transcribes it with OpenAI audio transcription.
- Images: decrypts, extracts OCR with Tesseract, and sends high-fidelity image tiles plus the Tesseract hint to the OpenAI Responses API.
- Stickers: supported as image-key media when explicitly requested with `media_type=sticker`.
- Documents: decrypts, saves files locally, and returns Tesseract plus OpenAI OCR.
- Videos: runs a base64-encoded `ffmpeg` command for automation-driven processing.

## Configuration

- `openai_api_key`: OpenAI API key used for audio transcription and image OCR/analysis.
- `audio_model`: OpenAI transcription model. Defaults to `whisper-1`.
- `image_model`: OpenAI image OCR and analysis model. Defaults to `gpt-5.5`.
- `image_max_output_tokens`: Maximum generated output tokens for image OCR and analysis. Defaults to `20000` and maps to the Responses API `max_output_tokens` parameter.
- `tesseract_languages`: Tesseract OCR languages. Defaults to `eng+heb`.
- `save_dir`: Default directory where decrypted documents are saved. Use a Paperless consume directory here if documents should be sent to Paperless.
- `document_model`: Optional OpenAI model for document OCR. Leave empty to use `image_model`.
- `document_max_output_tokens`: Maximum generated output tokens for document OCR.
- `document_ocr_max_pages`: Maximum number of document pages to OCR.

## Companion Integration

Install the custom integration from this repository after starting the add-on. It exposes these Home Assistant actions:

- `whatsapp_media_processor.process_audio`
- `whatsapp_media_processor.process_document`
- `whatsapp_media_processor.process_image`
- `whatsapp_media_processor.process_video`

The integration finds this add-on through Home Assistant Supervisor discovery. It does not require an IP address or port during setup.

See [DOCS.md](./DOCS.md) for internal endpoint details and [the repository README](../README.md) for installation and automation examples.

## Runtime Notes

The add-on exposes an internal HTTP API on port `9000` for the companion integration. The port is not published as a LAN endpoint by default.
