# Contributing to WhatsApp Media Processor for Home Assistant

Thanks for your interest in improving WhatsApp Media Processor.

This project contains a Home Assistant add-on and a companion custom integration. The add-on decrypts and processes WhatsApp media. The integration exposes Home Assistant actions and discovers the add-on through Supervisor.

Contributions are welcome, including bug reports, documentation improvements, compatibility fixes, security hardening, integration improvements, and automation examples.

## Before You Start

Please open an issue before starting large or risky changes. This helps avoid duplicated work and gives maintainers a chance to discuss the approach first.

Small fixes, documentation updates, and clearly scoped bug fixes can usually go straight to a pull request.

## Reporting Bugs

When reporting a bug, please include:

- The WhatsApp Media Processor version you are using.
- Your Home Assistant version.
- Whether you installed through the add-on store, HACS, manually, or from a development branch.
- Your Home Assistant host type.
- The affected action or add-on feature.
- Clear steps to reproduce the issue.
- Relevant Home Assistant, add-on, or integration logs with sensitive information removed.
- What you expected to happen.
- What actually happened.

Do not include real OpenAI keys, WhatsApp media keys, encrypted media URLs, phone numbers, private message content, private file paths, tokens, or personal Home Assistant configuration.

## Suggesting Features

Feature requests are welcome. Please describe:

- The Home Assistant workflow or automation you want to improve.
- Whether the change affects audio, document, image, sticker, video, add-on setup, integration setup, actions, diagnostics, or documentation.
- How the feature should work with the WhatsApp integration from `moryoav/ha-addons`, if relevant.
- Any privacy, security, cost, OpenAI usage, or file-write concerns.

## Development Setup

Clone the repository:

```bash
git clone https://github.com/moryoav/ha-whatsapp-decrypt.git
cd ha-whatsapp-decrypt
```

Repository layout:

```text
whatsapp_media_processor/                 Home Assistant add-on
custom_components/whatsapp_media_processor/  Home Assistant custom integration
hacs.json                                  HACS metadata
repository.yaml                            Home Assistant add-on repository metadata
```

For local Home Assistant testing:

1. Add this repository as an add-on repository.
2. Install and start the **WhatsApp Media Processor** add-on.
3. Copy or install `custom_components/whatsapp_media_processor`.
4. Restart Home Assistant.
5. Add **WhatsApp Media Processor** from **Settings** -> **Devices & services**.

## Pull Request Guidelines

Please keep pull requests focused. A good pull request should:

- Explain what changed and why.
- Mention any related issue.
- Keep unrelated formatting or refactoring out of the change.
- Update documentation when behavior, installation, options, actions, responses, diagnostics, or supported media types change.
- Include automation examples when changing action inputs or responses.
- Avoid committing secrets, credentials, private logs, phone numbers, media keys, encrypted media URLs, or private Home Assistant configuration.

If you change integration behavior, update `README.md`, `CHANGELOG.md`, `custom_components/whatsapp_media_processor/services.yaml`, `custom_components/whatsapp_media_processor/strings.json`, and translations where appropriate.

If you change add-on behavior, update `README.md`, `whatsapp_media_processor/README.md`, `whatsapp_media_processor/DOCS.md`, `whatsapp_media_processor/CHANGELOG.md`, and add-on translations where appropriate.

## Testing

Before opening a pull request, test the parts you changed as much as practical.

Useful local checks:

```powershell
python -m py_compile whatsapp_media_processor/server.py
python -m py_compile custom_components/whatsapp_media_processor/*.py
python -m json.tool custom_components/whatsapp_media_processor/manifest.json
python -m json.tool custom_components/whatsapp_media_processor/strings.json
```

For integration changes, verify that Home Assistant can:

- Load the `whatsapp_media_processor` integration.
- Complete the config flow after the add-on is running.
- Call the affected action with a `response_variable`.
- Reload or restart without relevant errors.

For add-on changes, verify the affected media path:

- Audio transcription returns usable `text`.
- Document processing saves the expected file.
- Image and sticker processing return `text` or `output_text`.
- Video processing returns expected output metadata when a valid prepared `ffmpeg` command is supplied.

For documentation-only changes, check that links, paths, examples, and Home Assistant UI names are accurate.

## Security Notes

Please use extra care when changing:

- Handling of WhatsApp media keys and encrypted media URLs.
- OpenAI API key access and logging.
- Downloading, decrypting, resizing, transcribing, or analyzing user media.
- File writes under `/share` or the configured Paperless consume directory.
- Home Assistant action schemas and service response data.
- Add-on health checks and Supervisor discovery.

If you believe you found a security vulnerability, do not open a public issue with exploit details. Follow `SECURITY.md`.

## Documentation

Please update documentation when changing user-facing behavior. Depending on the change, this may include:

- `README.md`
- `whatsapp_media_processor/README.md`
- `whatsapp_media_processor/DOCS.md`
- `whatsapp_media_processor/CHANGELOG.md`
- `custom_components/whatsapp_media_processor/README.md`
- `custom_components/whatsapp_media_processor/services.yaml`
- `custom_components/whatsapp_media_processor/strings.json`
- `custom_components/whatsapp_media_processor/translations/en.json`

Use plain, direct language and include Home Assistant examples where they make the workflow easier to understand.
