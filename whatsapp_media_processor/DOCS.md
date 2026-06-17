# WhatsApp Media Processor Documentation

The add-on exposes a small HTTP API on port `9000`. It auto-routes requests based on the query parameters you send.

The optional `media_type` query parameter can be one of `image`, `sticker`, `audio`, `video`, or `document`. Numeric values `1` through `5` are also accepted for compatibility with the old decryptor.

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

The decryption logic is implemented inside the Python add-on process. It supports the same raw 32-byte media key and protobuf media-key blob formats handled by the old Go tool. Sticker media is treated as image-key media, matching current WhatsApp Web client library behavior.
