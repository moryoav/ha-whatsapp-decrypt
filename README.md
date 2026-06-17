# WhatsApp Media Processor Add-ons

Home Assistant add-on repository and companion custom integration for processing encrypted WhatsApp media from automations.

## Add-on Installation

1. In Home Assistant, go to **Settings** > **Add-ons** > **Add-on Store**.
2. Open the three-dot menu and select **Repositories**.
3. Add this repository URL:

   ```text
   https://github.com/moryoav/ha-whatsapp-decrypt
   ```

4. Install **WhatsApp Media Processor**.
5. Set the add-on options, especially `openai_api_key`.
6. Start the add-on.

## Custom Integration Installation

The custom integration replaces `rest_command` entries with service actions.

1. Copy [custom_components/whatsapp_media_processor](./custom_components/whatsapp_media_processor) into `/config/custom_components/whatsapp_media_processor` in Home Assistant, or install this repository as a HACS custom integration.
2. Restart Home Assistant.
3. Go to **Settings** > **Devices & services** > **Add integration**.
4. Add **WhatsApp Media Processor**.
5. Enter the add-on base URL, for example:

   ```text
   http://192.168.1.229:9000
   ```

The integration exposes these actions:

- `whatsapp_media_processor.process_audio`
- `whatsapp_media_processor.process_document`
- `whatsapp_media_processor.process_image`
- `whatsapp_media_processor.process_video`

## Included Add-on

- [WhatsApp Media Processor](./whatsapp_media_processor) decrypts WhatsApp audio, images, documents, and video-processing requests for Home Assistant automations.

## Notes

- Image analysis uses the OpenAI Responses API.
- WhatsApp media decryption is built into the add-on; no external decryptor repository is pulled during the image build.
- The default image model is `gpt-5.4-mini`.
- The add-on exposes an HTTP API on port `9000`.
