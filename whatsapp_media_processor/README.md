# WhatsApp Media Processor

Decrypts WhatsApp media and prepares it for Home Assistant automations.

## What It Handles

- Audio: decrypts WhatsApp audio and transcribes it with OpenAI audio transcription.
- Images: decrypts, resizes, and analyzes images with the OpenAI Responses API.
- Documents: decrypts and saves files to a Paperless consume directory.
- Videos: runs a base64-encoded `ffmpeg` command for automation-driven processing.

## Configuration

- `openai_api_key`: OpenAI API key used for audio transcription and image analysis.
- `audio_model`: OpenAI transcription model. Defaults to `whisper-1`.
- `image_model`: OpenAI image-analysis model. Defaults to `gpt-5.4-mini`.
- `image_max_output_tokens`: Maximum generated output tokens for image analysis. This maps to the Responses API `max_output_tokens` parameter.
- `paperless_consume_dir`: Directory where decrypted documents are saved.

See [DOCS.md](./DOCS.md) for endpoint details and automation notes.
