# Changelog

## 1.6.0

- Reworked the repository README around the current add-on and companion integration workflow.
- Added Home Assistant and HACS installation buttons.
- Added contributor, support, security, conduct, issue template, pull request template, and MIT license files for the GitHub community checklist.
- Expanded automation examples for `new_whatsapp_message` events from the companion WhatsApp integration.

## 1.5.0

- Added Home Assistant custom integration brand assets under `custom_components/whatsapp_media_processor/brand`.
- Added custom integration translations under `custom_components/whatsapp_media_processor/translations`.

## 1.4.0

- Changed the add-on/integration connection model to Supervisor discovery.
- Removed the published LAN port mapping; direct `rest_command` calls to `http://<home_assistant_ip>:9000` are no longer supported.
- Added Supervisor discovery registration from the add-on runtime.
- Updated the custom integration config flow to automatically find the installed add-on without asking for URL or port.

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
