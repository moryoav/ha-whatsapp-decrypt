import os
import re
import json
import base64
import shlex
import logging
import subprocess
import urllib.request

from flask import Flask, request, jsonify, Response
from openai import OpenAI
from PIL import Image

app = Flask(__name__)

TMP_DIR = "/config/tmp"
OPTIONS_PATH = "/data/options.json"
WHATSAPP_DECRYPT_BIN = "/go/bin/whatsapp-media-decrypt"

DEFAULT_PAPERLESS_DIR = "/share/Paperless_ngx_consume"
DEFAULT_IMAGE_MODEL = "gpt-5.4-mini"
DEFAULT_IMAGE_MAX_OUTPUT_TOKENS = 12000

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


def decode_code_to_hex(code):
    decoded_code = base64.b64decode(code)
    return "".join(f"{byte:02x}" for byte in decoded_code)


def decrypt_whatsapp_file(code, url, media_type, output_path):
    """
    WhatsApp media types used by whatsapp-media-decrypt:
    1 = image
    2 = video
    3 = audio
    4 = document
    """
    if not code or not url:
        raise ValueError("Missing 'code' or 'url' parameter")

    hex_code = decode_code_to_hex(code)

    enc_file_path = os.path.join(TMP_DIR, "file.enc")
    download_file(url, enc_file_path)

    cmd = [
        WHATSAPP_DECRYPT_BIN,
        "-o", output_path,
        "-t", str(media_type),
        enc_file_path,
        hex_code,
    ]

    logging.info("Decrypting WhatsApp media type %s to %s", media_type, output_path)
    subprocess.run(cmd, check=True)

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

    paperless_dir = get_option("paperless_consume_dir", DEFAULT_PAPERLESS_DIR)
    os.makedirs(paperless_dir, exist_ok=True)

    decrypted_file_path = os.path.join(paperless_dir, filename)

    decrypt_whatsapp_file(
        code=code,
        url=url,
        media_type=4,
        output_path=decrypted_file_path,
    )

    return jsonify({
        "message": "File decrypted and saved",
        "file": decrypted_file_path,
    }), 200


def process_audio():
    code = request.args.get("code")
    url = request.args.get("url")

    decrypted_file_path = os.path.join(TMP_DIR, "file.ogg")

    decrypt_whatsapp_file(
        code=code,
        url=url,
        media_type=3,
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

    if not user_text:
        return jsonify({"error": "Missing 'text' parameter for image processing"}), 400

    decrypted_file_path = os.path.join(TMP_DIR, "file.jpg")

    decrypt_whatsapp_file(
        code=code,
        url=url,
        media_type=1,
        output_path=decrypted_file_path,
    )

    resize_image(decrypted_file_path)
    base64_image = encode_image_base64(decrypted_file_path)

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
                        "image_url": f"data:image/jpeg;base64,{base64_image}",
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

        # Auto-routing without adding a new explicit type parameter.
        if request.args.get("ffmpeg"):
            return process_video_ffmpeg()

        if request.args.get("filename"):
            return process_document()

        if request.args.get("text"):
            return process_image()

        return process_audio()

    except subprocess.CalledProcessError as e:
        logging.exception("Subprocess failed")
        return jsonify({"error": f"Subprocess error: {str(e)}"}), 500

    except Exception as e:
        logging.exception("Unexpected error")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ensure_dirs()
    app.run(host="0.0.0.0", port=9000)
