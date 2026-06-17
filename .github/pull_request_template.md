## Summary

Describe what this pull request changes and why.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Security hardening
- [ ] Maintenance or refactoring
- [ ] Other

## Affected Area

- [ ] Add-on startup or configuration
- [ ] Integration setup or discovery
- [ ] Audio action
- [ ] Document action
- [ ] Image or sticker action
- [ ] Video action
- [ ] OpenAI request or response
- [ ] File save or Paperless consume directory
- [ ] Diagnostics or logs
- [ ] Documentation or examples

## Testing

Describe the testing you performed.

- [ ] `python -m py_compile whatsapp_media_processor/server.py`
- [ ] `python -m py_compile custom_components/whatsapp_media_processor/*.py`
- [ ] Home Assistant loads or restarts without relevant errors.
- [ ] The `whatsapp_media_processor` integration can be set up or reloaded when affected.
- [ ] Relevant actions were tested with `response_variable`.
- [ ] Add-on startup and health check were tested when affected.
- [ ] Documentation-only change; no runtime testing needed.

## Security and Privacy

- [ ] This change does not add secrets, tokens, OpenAI keys, WhatsApp media keys, encrypted media URLs, phone numbers, private message content, logs, or personal Home Assistant configuration.
- [ ] I considered whether this affects media downloads, decryption, OpenAI calls, file writes, `ffmpeg`, service responses, diagnostics, or Supervisor discovery.
- [ ] I updated `SECURITY.md` or documentation if this changes security-sensitive behavior.

## Documentation

- [ ] I updated relevant documentation, examples, or release notes.
- [ ] Documentation is not needed for this change.

## Related Issues

Link any related issues here.
