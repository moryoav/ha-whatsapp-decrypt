# Changelog

## 1.3.0

- Added a `/health` endpoint for custom integration setup checks.
- Added a companion Home Assistant custom integration in this repository.

## 1.2.0

- Replaced the external Go `whatsapp-media-decrypt` binary with built-in Python media decryption.
- Removed the Docker build dependency on `github.com/ddz/whatsapp-media-decrypt@latest`.
- Added explicit `media_type` parsing for image, sticker, audio, video, and document requests.
- Treated stickers as image-key media instead of using the unverified `WhatsApp Sticker Keys` fork change.
- Reduced Docker image build dependencies by removing Go and Git.

## 1.1.0

- Migrated image analysis from Chat Completions to the OpenAI Responses API.
- Updated the default image model to `gpt-5.4-mini`.
- Replaced the old hardcoded image token cap with configurable `image_max_output_tokens`.
- Added Responses API output helpers while preserving `choices[0].message.content` compatibility for older Home Assistant templates.
- Converted the project into a Home Assistant add-on repository layout with `repository.yaml`, docs, and presentation assets.

## 1.0.2

- Existing local add-on version before repository packaging.
