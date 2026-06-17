# Changelog

## 1.1.0

- Migrated image analysis from Chat Completions to the OpenAI Responses API.
- Updated the default image model to `gpt-5.4-mini`.
- Replaced the old hardcoded image token cap with configurable `image_max_output_tokens`.
- Added Responses API output helpers while preserving `choices[0].message.content` compatibility for older Home Assistant templates.
- Converted the project into a Home Assistant add-on repository layout with `repository.yaml`, docs, and presentation assets.

## 1.0.2

- Existing local add-on version before repository packaging.
