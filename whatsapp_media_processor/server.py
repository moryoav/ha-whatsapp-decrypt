import os
import re
import json
import base64
import hashlib
import hmac
import shlex
import logging
import subprocess
import tempfile
import urllib.request

from flask import Flask, request, jsonify, Response
from openai import OpenAI
from PIL import Image
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

app = Flask(__name__)

TMP_DIR = "/config/tmp"
OPTIONS_PATH = "/data/options.json"

DEFAULT_PAPERLESS_DIR = "/share/Paperless_ngx_consume"
DEFAULT_IMAGE_MODEL = "gpt-5.4-mini"
DEFAULT_IMAGE_MAX_OUTPUT_TOKENS = 12000

MEDIA_TYPE_IMAGE = 1
MEDIA_TYPE_VIDEO = 2
MEDIA_TYPE_AUDIO = 3
MEDIA_TYPE_DOCUMENT = 4
MEDIA_TYPE_STICKER = 5

MEDIA_TYPE_ALIASES = {
    "1": MEDIA_TYPE_IMAGE,
    "image": MEDIA_TYPE_IMAGE,
    "photo": MEDIA_TYPE_IMAGE,
    "2": MEDIA_TYPE_VIDEO,
    "video": MEDIA_TYPE_VIDEO,
    "3": MEDIA_TYPE_AUDIO,
    "audio": MEDIA_TYPE_AUDIO,
    "ptt": MEDIA_TYPE_AUDIO,
    "voice": MEDIA_TYPE_AUDIO,
    "4": MEDIA_TYPE_DOCUMENT,
    "doc": MEDIA_TYPE_DOCUMENT,
    "document": MEDIA_TYPE_DOCUMENT,
    "5": MEDIA_TYPE_STICKER,
    "sticker": MEDIA_TYPE_STICKER,
}

MEDIA_TYPE_NAMES = {
    MEDIA_TYPE_IMAGE: "image",
    MEDIA_TYPE_VIDEO: "video",
    MEDIA_TYPE_AUDIO: "audio",
    MEDIA_TYPE_DOCUMENT: "document",
    MEDIA_TYPE_STICKER: "sticker",
}

MEDIA_APP_INFO = {
    MEDIA_TYPE_IMAGE: b"WhatsApp Image Keys",
    MEDIA_TYPE_VIDEO: b"WhatsApp Video Keys",
    MEDIA_TYPE_AUDIO: b"WhatsApp Audio Keys",
    MEDIA_TYPE_DOCUMENT: b"WhatsApp Document Keys",
    # WhatsApp Web libraries route sticker media through image keys.
    MEDIA_TYPE_STICKER: b"WhatsApp Image Keys",
}

IMAGE_MIME_TYPES = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}

IMAGE_ANALYSIS_INSTRUCTIONS = (
    "You are an image-analysis step inside a Home Assistant WhatsApp automation. "
    "Your job is ONLY to analyze the image and extract useful information for a later, "
    "tool-enabled assistant. "
    "Do NOT perform any action requested by the user. "
    "Do NOT claim that you added, saved, edited, filed, sent, updated, or changed anything. "
    "Do NOT reply conversationally to the user. "
    "Instead, return a clear structured extraction of the image contents for downstream processing.\n\n"
    "Rules:\n"
    "1. Use the user's caption/request only as context for interpreting the image.\n"
    "2. If the image contains text, transcribe it as accurately as possible.\n"
    "3. If the image appears to contain a recipe, extract as many of the following as possible:\n"
    "   - title\n"
    "   - short description\n"
    "   - ingredients\n"
    "   - quantities\n"
    "   - steps/instructions\n"
    "   - prep time\n"
    "   - cook time\n"
    "   - servings\n"
    "   - notes\n"
    "   - any visible source text\n"
    "4. If some information is unclear, say so explicitly instead of guessing.\n"
    "5. Return the result in plain text using this exact structure:\n\n"
    "User caption/request:\n"
    "<caption>\n\n"
    "Image type:\n"
    "<what kind of image this is>\n\n"
    "Extracted content:\n"
    "<structured extraction>\n\n"
    "Relevant text seen in image:\n"
    "<ocr/transcription>\n\n"
    "Important ambiguities or missing details:\n"
    "<ambiguities>"
)


def load_options():
    if not os.path.exists(OPTIONS_PATH):
        return {}

    with open(OPTIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_openai_client():
    options = load_options()
    api_key = options.get("openai_api_key")

    if not api_key:
        raise RuntimeError("Missing openai_api_key in addon options")

    return OpenAI(api_key=api_key)


def get_option(name, default=None):
    return load_options().get(name, default)


def get_int_option(name, default):
    value = get_option(name, default)

    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc

    if parsed < 1:
        raise ValueError(f"{name} must be greater than zero")

    return parsed


def ensure_dirs():
    os.makedirs(TMP_DIR, exist_ok=True)

    paperless_dir = get_option("paperless_consume_dir", DEFAULT_PAPERLESS_DIR)
    os.makedirs(paperless_dir, exist_ok=True)


def download_file(url, output_path):
    urllib.request.urlretrieve(url, output_path)


def get_request_media_type(default=None):
    media_type = (
        request.args.get("media_type")
        or request.args.get("mediaType")
        or request.args.get("type")
    )

    if not media_type:
        return default

    parsed = MEDIA_TYPE_ALIASES.get(media_type.strip().lower())
    if parsed is None:
        allowed = ", ".join(sorted(MEDIA_TYPE_ALIASES))
        raise ValueError(f"Unsupported media_type '{media_type}'. Use one of: {allowed}")

    return parsed


def decode_media_key_code(code):
    if not code:
        raise ValueError("Missing 'code' parameter")

    normalized = code.strip().replace(" ", "+")
    normalized += "=" * (-len(normalized) % 4)

    return base64.urlsafe_b64decode(normalized)


def read_proto_varint(data, offset):
    result = 0
    shift = 0

    while offset < len(data):
        byte = data[offset]
        offset += 1
        result |= (byte & 0x7F) << shift

        if byte < 0x80:
            return result, offset

        shift += 7
        if shift > 63:
            raise ValueError("Invalid protobuf varint")

    raise ValueError("Unexpected end of protobuf varint")


def parse_media_key_blob(media_key_blob):
    if len(media_key_blob) == 32:
        return media_key_blob, None

    media_key = None
    file_hash = None
    offset = 0

    while offset < len(media_key_blob):
        key, offset = read_proto_varint(media_key_blob, offset)
        field_number = key >> 3
        wire_type = key & 0x07

        if wire_type == 0:
            _, offset = read_proto_varint(media_key_blob, offset)
            continue

        if wire_type != 2:
            raise ValueError(f"Unsupported media key protobuf wire type {wire_type}")

        length, offset = read_proto_varint(media_key_blob, offset)
        end = offset + length
        if end > len(media_key_blob):
            raise ValueError("Invalid media key protobuf length")

        value = media_key_blob[offset:end]
        offset = end

        if field_number == 1:
            media_key = value
        elif field_number == 2:
            file_hash = value

    if not media_key:
        raise ValueError("Could not find media key in protobuf blob")

    return media_key, file_hash


def expand_media_key(media_key, media_type):
    app_info = MEDIA_APP_INFO.get(media_type)
    if app_info is None:
        raise ValueError(f"Unsupported media type {media_type}")

    if len(media_key) != 32:
        raise ValueError(f"mediaKey length {len(media_key)} != 32")

    return HKDF(
        algorithm=hashes.SHA256(),
        length=112,
        salt=None,
        info=app_info,
    ).derive(media_key)


def decrypt_media_data(enc_file_data, media_key_blob, media_type):
    media_key, file_hash = parse_media_key_blob(media_key_blob)

    if file_hash:
        enc_file_hash = hashlib.sha256(enc_file_data).digest()
        if not hmac.compare_digest(enc_file_hash, file_hash):
            raise ValueError(".enc file hash does not match mediaKey")

    expanded_key = expand_media_key(media_key, media_type)
    iv = expanded_key[0:16]
    cipher_key = expanded_key[16:48]
    mac_key = expanded_key[48:80]

    if len(enc_file_data) <= 10:
        raise ValueError("Encrypted file is too short")

    encrypted_data = enc_file_data[:-10]
    media_mac = enc_file_data[-10:]
    expected_mac = hmac.new(
        mac_key,
        iv + encrypted_data,
        hashlib.sha256,
    ).digest()[:10]

    if not hmac.compare_digest(expected_mac, media_mac):
        media_name = MEDIA_TYPE_NAMES.get(media_type, str(media_type))
        raise ValueError(f"Invalid media HMAC for {media_name}")

    decryptor = Cipher(
        algorithms.AES(cipher_key),
        modes.CBC(iv),
    ).decryptor()
    padded_data = decryptor.update(encrypted_data) + decryptor.finalize()

    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    return unpadder.update(padded_data) + unpadder.finalize()


def decrypt_whatsapp_file(code, url, media_type, output_path):
    """
    1 = image
    2 = video
    3 = audio
    4 = document
    5 = sticker, decrypted with WhatsApp image keys
    """
    if not code or not url:
        raise ValueError("Missing 'code' or 'url' parameter")

    media_key_blob = decode_media_key_code(code)

    fd, enc_file_path = tempfile.mkstemp(suffix=".enc", dir=TMP_DIR)
    os.close(fd)

    try:
        download_file(url, enc_file_path)

        with open(enc_file_path, "rb") as enc_file:
            enc_file_data = enc_file.read()

        data = decrypt_media_data(enc_file_data, media_key_blob, media_type)

        with open(output_path, "wb") as output_file:
            output_file.write(data)
    finally:
        try:
            os.remove(enc_file_path)
        except FileNotFoundError:
            pass

    logging.info("Decrypted WhatsApp media type %s to %s", media_type, output_path)

    return output_path


def sanitize_filename(filename):
    if not filename:
        return "document"

    filename = filename.replace(" ", "_")

    # Keep English, Hebrew, numbers, underscore, dot, dash.
    filename = re.sub(r"[^a-zA-Z0-9א-ת_.-]", "", filename)

    # Avoid empty or unsafe names.
    filename = filename.strip("._-")
    if not filename:
        filename = "document"

    return filename


def resize_image(image_path):
    with Image.open(image_path) as img:
        short_side = min(img.size)
        long_side = max(img.size)

        if short_side > 768 or long_side > 2000:
            ratio = min(768 / short_side, 2000 / long_side)
            new_size = (
                int(img.size[0] * ratio),
                int(img.size[1] * ratio),
            )
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            img.save(image_path)


def get_image_mime_type(image_path):
    with Image.open(image_path) as img:
        return IMAGE_MIME_TYPES.get(img.format, "image/jpeg")


def encode_image_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def extract_output_text(response_payload):
    output_parts = []

    for output_item in response_payload.get("output", []):
        for content_item in output_item.get("content", []):
            if content_item.get("type") == "output_text" and content_item.get("text"):
                output_parts.append(content_item["text"])

    return "\n".join(output_parts).strip()


def build_image_response_payload(response):
    payload = response.model_dump()
    output_text = getattr(response, "output_text", None) or extract_output_text(payload)

    payload["output_text"] = output_text
    payload["text"] = output_text

    # Keep old Home Assistant templates that read choices[0].message.content working.
    payload["choices"] = [
        {
            "message": {
                "role": "assistant",
                "content": output_text,
            },
        },
    ]

    return payload


def process_video_ffmpeg():
    user_id = request.args.get("userId")
    ffmpeg_encoded = request.args.get("ffmpeg", default="")

    if not ffmpeg_encoded:
        return jsonify({"error": "Missing required 'ffmpeg' parameter"}), 400

    ffmpeg_cmd = base64.b64decode(ffmpeg_encoded).decode("utf-8")
    args = shlex.split(ffmpeg_cmd)

    if not args:
        return jsonify({"error": "Empty ffmpeg command"}), 400

    if args[0] != "ffmpeg":
        return jsonify({"error": "Command must start with ffmpeg"}), 400

    if "-y" not in args:
        args.insert(1, "-y")

    output_filename = None
    for token in reversed(args):
        if not token.startswith("-"):
            output_filename = token
            break

    if not output_filename:
        return jsonify({"error": "Could not determine output filename"}), 400

    logging.info("Running ffmpeg command: %s", " ".join(args))

    result = subprocess.run(
        args,
        shell=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logging.error("ffmpeg failed: %s", result.stderr)
        return jsonify({
            "error": "ffmpeg command failed",
            "details": result.stderr,
        }), 500

    return jsonify({
        "files": [output_filename],
        "user": user_id,
    }), 200


def process_document():
    code = request.args.get("code")
    url = request.args.get("url")
    filename = sanitize_filename(request.args.get("filename"))
    media_type = get_request_media_type(MEDIA_TYPE_DOCUMENT)

    paperless_dir = get_option("paperless_consume_dir", DEFAULT_PAPERLESS_DIR)
    os.makedirs(paperless_dir, exist_ok=True)

    decrypted_file_path = os.path.join(paperless_dir, filename)

    decrypt_whatsapp_file(
        code=code,
        url=url,
        media_type=media_type,
        output_path=decrypted_file_path,
    )

    return jsonify({
        "message": "File decrypted and saved",
        "file": decrypted_file_path,
    }), 200


def process_audio():
    code = request.args.get("code")
    url = request.args.get("url")
    media_type = get_request_media_type(MEDIA_TYPE_AUDIO)

    if media_type != MEDIA_TYPE_AUDIO:
        raise ValueError("Audio transcription only supports audio media")

    decrypted_file_path = os.path.join(TMP_DIR, "file.ogg")

    decrypt_whatsapp_file(
        code=code,
        url=url,
        media_type=media_type,
        output_path=decrypted_file_path,
    )

    client = get_openai_client()
    audio_model = get_option("audio_model", "whisper-1")

    with open(decrypted_file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model=audio_model,
            file=audio_file,
        )

    return Response(transcription.text, status=200, mimetype="text/plain")


def process_image():
    code = request.args.get("code")
    url = request.args.get("url")
    user_text = request.args.get("text")
    media_type = get_request_media_type(MEDIA_TYPE_IMAGE)

    if media_type not in (MEDIA_TYPE_IMAGE, MEDIA_TYPE_STICKER):
        raise ValueError("Image processing only supports image or sticker media")

    if not user_text:
        return jsonify({"error": "Missing 'text' parameter for image processing"}), 400

    file_extension = "webp" if media_type == MEDIA_TYPE_STICKER else "jpg"
    decrypted_file_path = os.path.join(TMP_DIR, f"file.{file_extension}")

    decrypt_whatsapp_file(
        code=code,
        url=url,
        media_type=media_type,
        output_path=decrypted_file_path,
    )

    resize_image(decrypted_file_path)
    base64_image = encode_image_base64(decrypted_file_path)
    image_mime_type = get_image_mime_type(decrypted_file_path)

    client = get_openai_client()
    image_model = get_option("image_model", DEFAULT_IMAGE_MODEL)
    image_max_output_tokens = get_int_option(
        "image_max_output_tokens",
        DEFAULT_IMAGE_MAX_OUTPUT_TOKENS,
    )

    response = client.responses.create(
        model=image_model,
        instructions=IMAGE_ANALYSIS_INSTRUCTIONS,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"User caption/request:\n{user_text}",
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:{image_mime_type};base64,{base64_image}",
                    },
                ],
            },
        ],
        max_output_tokens=image_max_output_tokens,
        store=False,
    )

    return jsonify(build_image_response_payload(response)), 200


@app.route("/", methods=["GET"])
def process_request():
    try:
        ensure_dirs()
        media_type = get_request_media_type()

        # Auto-routing without adding a new explicit type parameter.
        if request.args.get("ffmpeg"):
            return process_video_ffmpeg()

        if request.args.get("filename"):
            return process_document()

        if request.args.get("text"):
            return process_image()

        if media_type in (MEDIA_TYPE_IMAGE, MEDIA_TYPE_STICKER):
            return jsonify({
                "error": "Missing 'text' parameter for image or sticker processing",
            }), 400

        if media_type == MEDIA_TYPE_DOCUMENT:
            return process_document()

        if media_type == MEDIA_TYPE_VIDEO:
            return jsonify({
                "error": "Video processing requires the 'ffmpeg' parameter",
            }), 400

        return process_audio()

    except Exception as e:
        logging.exception("Unexpected error")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ensure_dirs()
    app.run(host="0.0.0.0", port=9000)
