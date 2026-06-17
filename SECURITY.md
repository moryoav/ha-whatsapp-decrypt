# Security Policy

WhatsApp Media Processor handles encrypted media URLs, WhatsApp media keys, OpenAI credentials, decrypted files, and Home Assistant automation data. Please treat security, privacy, and diagnostics issues with care.

## Supported Versions

Security fixes are intended for the latest published release and the current `main` branch.

Older releases are not actively supported unless a maintainer says otherwise in a specific issue or release note.

## Reporting a Vulnerability

Please do not open a public issue with exploit details, working proof-of-concept code, private logs, tokens, OpenAI keys, WhatsApp media keys, encrypted media URLs, phone numbers, message contents, or personal Home Assistant configuration.

If GitHub private vulnerability reporting is available for this repository, use the **Report a vulnerability** button on the Security tab.

If private vulnerability reporting is not available, open a minimal public issue that says you have a security concern and asks the maintainer to arrange private disclosure. Do not include sensitive details in that issue.

## What to Include

When reporting a vulnerability privately, include as much of the following as you can safely share:

- A clear description of the issue.
- The affected version or commit.
- Whether the issue affects the add-on, custom integration, Supervisor discovery, action schemas, file writes, OpenAI calls, media decryption, or logs.
- Steps to reproduce in a safe test environment.
- The expected impact.
- Any relevant logs with secrets and private configuration removed.
- Suggested mitigations, if you know them.

## Security-Sensitive Areas

Please use extra care when changing or reviewing:

- WhatsApp media key and encrypted URL handling.
- Downloading and decrypting remote media.
- OpenAI API key access and request/response logging.
- Image resizing, document saves, audio transcription, and video command handling.
- `ffmpeg` command validation.
- File writes under `/share`, `/config`, or the configured Paperless consume directory.
- Home Assistant service responses and diagnostics.
- Add-on health checks and Supervisor discovery.

## Responsible Testing

Test security reports and fixes only in an environment you own or have permission to use. Do not attempt to access, modify, disrupt, or disclose another person's Home Assistant instance, WhatsApp account, media, credentials, logs, or configuration.

## Public Disclosure

Please give the maintainer reasonable time to investigate and fix confirmed vulnerabilities before publishing details publicly. Coordinated disclosure helps protect users while a fix is prepared.
