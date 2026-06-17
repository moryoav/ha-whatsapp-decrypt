# WhatsApp Media Processor Add-ons

Home Assistant add-on repository for processing encrypted WhatsApp media from automations.

## Installation

1. In Home Assistant, go to **Settings** > **Add-ons** > **Add-on Store**.
2. Open the three-dot menu and select **Repositories**.
3. Add this repository URL:

   ```text
   https://github.com/moryoav/ha-whatsapp-decrypt
   ```

4. Install **WhatsApp Media Processor**.
5. Set the add-on options, especially `openai_api_key`.
6. Start the add-on.

## Included Add-ons

- [WhatsApp Media Processor](./whatsapp_media_processor) decrypts WhatsApp audio, images, documents, and video-processing requests for Home Assistant automations.

## Notes

- Image analysis uses the OpenAI Responses API.
- WhatsApp media decryption is built into the add-on; no external decryptor repository is pulled during the image build.
- The default image model is `gpt-5.4-mini`.
- The add-on exposes an HTTP API on port `9000`.
