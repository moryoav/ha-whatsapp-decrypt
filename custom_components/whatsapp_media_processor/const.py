DOMAIN = "whatsapp_media_processor"

CONF_BASE_URL = "base_url"
CONF_URL = "url"

ADDON_DISCOVERY_SERVICE = DOMAIN
ADDON_PORT = 9000
ADDON_NAME = "WhatsApp Media Processor"
ADDON_SLUG = "whatsapp_media_processor"
ADDON_REPOSITORY = "moryoav/ha-whatsapp-decrypt"
ADDON_FALLBACK_HOSTS = (
    "whatsapp-media-processor",
    "whatsapp_media_processor",
)

DEFAULT_AUDIO_TIMEOUT = 90
DEFAULT_DOCUMENT_TIMEOUT = 90
DEFAULT_IMAGE_TIMEOUT = 90
DEFAULT_VIDEO_TIMEOUT = 180

SERVICE_PROCESS_AUDIO = "process_audio"
SERVICE_PROCESS_DOCUMENT = "process_document"
SERVICE_PROCESS_IMAGE = "process_image"
SERVICE_PROCESS_VIDEO = "process_video"

ATTR_CODE = "code"
ATTR_URL = "url"
ATTR_FILENAME = "filename"
ATTR_TEXT = "text"
ATTR_FFMPEG = "ffmpeg"
ATTR_USER_ID = "user_id"
ATTR_MEDIA_TYPE = "media_type"
ATTR_TIMEOUT = "timeout"

DATA_SERVICES_REGISTERED = "services_registered"
