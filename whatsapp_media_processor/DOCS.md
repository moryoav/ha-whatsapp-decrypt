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

Send `code`, `url`, and `text` query parameters. Optionally include `image_mode=auto`, `image_mode=strict_ocr`, or `image_mode=visual_analysis`; `auto` is the default.

```text
GET /?code=<base64_media_key>&url=<encrypted_media_url>&text=<caption_or_request>&image_mode=auto
```

For stickers, include `media_type=sticker` and `text`:

```text
GET /?code=<base64_media_key>&url=<encrypted_sticker_url>&media_type=sticker&text=<caption_or_request>
```

The image is decrypted, then Tesseract OCR runs first. OpenAI receives the Tesseract text as an untrusted hint plus ordered high-fidelity image tiles. Long screenshots are tiled with overlap instead of being downscaled to a tiny single image. Recipe, translation, OCR, receipt, document, and other text-heavy requests use `strict_ocr`, which returns source-language transcription only; downstream automations can translate or act on that text later. The response JSON includes:

- `text`: labeled combined output with separate `Tesseract OCR` and `OpenAI OCR and image analysis` sections.
- `combined_text`: same value as `text`, for easier Home Assistant templates.
- `tesseract_text`: raw OCR text returned by Tesseract.
- `tesseract_error`: error text if Tesseract OCR failed; otherwise `null`.
- `openai_output_text`: formatted OpenAI OCR/analysis output for automations.
- `openai_text`: same value as `openai_output_text`.
- `openai_raw_output_text`: raw aggregated Responses API text before compatibility formatting.
- `openai_error`: error text if OpenAI image OCR failed; otherwise `null`.
- `openai_mode`: resolved mode, either `strict_ocr` or `visual_analysis`.
- `openai_requested_mode`: requested mode, usually `auto`.
- `image_processing`: original image dimensions, tile count, detail level metadata, and tile bounds.
- `ocr`: structured object with separate `tesseract` and `openai` entries.
- `output_text`: same labeled combined output as `text`.
- `choices[0].message.content`: compatibility field for older Chat Completions-style templates.
- Native Responses API fields such as `id`, `status`, `output`, and `usage`.

## Audio Transcription

Send `code` and `url` without `text`, `filename`, or `ffmpeg`.

```text
GET /?code=<base64_media_key>&url=<encrypted_media_url>
```

The add-on returns the transcription as `text/plain`.

## Document Processing

Send `code`, `url`, and `filename`.

```text
GET /?code=<base64_media_key>&url=<encrypted_media_url>&filename=<safe_filename.pdf>
```

To save to a specific add-on-accessible folder, include `save_dir`:

```text
GET /?code=<base64_media_key>&url=<encrypted_media_url>&filename=<safe_filename.pdf>&save_dir=/share/Documents
```

The decrypted document is saved under the request `save_dir` when supplied, otherwise under the configured `save_dir`. The response JSON includes:

- `file` and `path`: saved document path.
- `filename`: sanitized saved filename.
- `save_dir`: directory used for the save.
- `text`: labeled combined output with separate `Tesseract OCR` and `OpenAI OCR and document analysis` sections.
- `combined_text`: same value as `text`.
- `tesseract_text`: raw OCR text returned by Tesseract.
- `tesseract_error`: error text if Tesseract OCR failed; otherwise `null`.
- `openai_output_text`: raw document OCR output from OpenAI.
- `openai_text`: same value as `openai_output_text`.
- `openai_error`: error text if OpenAI document OCR failed; otherwise `null`.
- `ocr`: structured object with separate `tesseract` and `openai` entries.
- `document`: detected document format, page count, processed page count, max pages, and truncation metadata.
- `choices[0].message.content`: compatibility field for older Chat Completions-style templates.

Document OCR supports PDFs and image documents. Unsupported document types are still saved and return OCR error fields.

## Video Processing

Send a base64-encoded `ffmpeg` command in the `ffmpeg` query parameter.

```text
GET /?ffmpeg=<base64_encoded_ffmpeg_command>&userId=<optional_user_id>
```

The command must start with `ffmpeg`. The add-on injects `-y` if it is missing.

## OpenAI Notes

Image OCR and analysis uses `client.responses.create(...)` with `input_text` and `input_image` content items. The configured token limit is sent as `max_output_tokens`, which is the Responses API parameter for generated output length. The add-on requests structured output when the installed OpenAI SDK supports it, and falls back to plain Responses output if the SDK or configured model rejects that parameter.

Tesseract OCR uses `eng+heb` by default, and this can be changed with the `tesseract_languages` add-on option.

Document OCR renders supported documents to page images, then sends copies of those page images to Tesseract and OpenAI in parallel. `document_ocr_max_pages` limits the number of pages processed. OpenAI document OCR uses `document_model` when set, otherwise `image_model`, and uses `document_max_output_tokens` for response length.

## Decryption Notes

The decryption logic is implemented inside the Python add-on process. It supports raw 32-byte media keys and protobuf media-key blobs. Sticker media is treated as image-key media, matching current WhatsApp Web client library behavior.
