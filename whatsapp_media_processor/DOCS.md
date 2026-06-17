# WhatsApp Media Processor Documentation

The add-on exposes a small internal HTTP API on port `9000`. It is meant for the companion Home Assistant integration and is not published to the LAN.

The optional `media_type` query parameter can be one of `image`, `sticker`, `audio`, `video`, or `document`. Numeric values `1` through `5` are also accepted.

Home Assistant automations should use the companion integration actions. The HTTP routes below document the add-on interface used by that integration.

## Health Check

```text
GET /health
```

Returns add-on health and version metadata for the companion custom integration setup flow.

## Image Analysis

Send `code`, `url`, and `text` query parameters.

```text
GET /?code=<base64_media_key>&url=<encrypted_media_url>&text=<caption_or_request>
```

For stickers, include `media_type=sticker` and `text`:

```text
GET /?code=<base64_media_key>&url=<encrypted_sticker_url>&media_type=sticker&text=<caption_or_request>
```

The image is decrypted, resized when needed, encoded as a data URL, and sent to OpenAI using the Responses API. The response JSON includes:

- `output_text`: aggregated Responses API text output.
- `text`: same value as `output_text`, for easier Home Assistant templates.
- `choices[0].message.content`: compatibility field for older Chat Completions-style templates.
- Native Responses API fields such as `id`, `status`, `output`, and `usage`.

## Audio Transcription

Send `code` and `url` without `text`, `filename`, or `ffmpeg`.

```text
GET /?code=<base64_media_key>&url=<encrypted_media_url>
```

The add-on returns the transcription as `text/plain`.

## Document Save

Send `code`, `url`, and `filename`.

```text
GET /?code=<base64_media_key>&url=<encrypted_media_url>&filename=<safe_filename.pdf>
```

The decrypted document is saved under `paperless_consume_dir`.

## Video Processing

Send a base64-encoded `ffmpeg` command in the `ffmpeg` query parameter.

```text
GET /?ffmpeg=<base64_encoded_ffmpeg_command>&userId=<optional_user_id>
```

The command must start with `ffmpeg`. The add-on injects `-y` if it is missing.

## OpenAI Notes

Image analysis uses `client.responses.create(...)` with `input_text` and `input_image` content items. The configured token limit is sent as `max_output_tokens`, which is the Responses API parameter for generated output length.

## Decryption Notes

The decryption logic is implemented inside the Python add-on process. It supports raw 32-byte media keys and protobuf media-key blobs. Sticker media is treated as image-key media, matching current WhatsApp Web client library behavior.
