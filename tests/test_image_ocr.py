import importlib.util
import json
import pathlib
import sys
import tempfile
import types
import unittest

from PIL import Image


if "pytesseract" not in sys.modules:
    sys.modules["pytesseract"] = types.SimpleNamespace(
        image_to_string=lambda *args, **kwargs: ""
    )


def load_server_module():
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    server_path = repo_root / "whatsapp_media_processor" / "server.py"
    spec = importlib.util.spec_from_file_location(
        "whatsapp_media_processor_test_server",
        server_path,
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


server = load_server_module()


class FakeResponse:
    def __init__(self, output_text):
        self.output_text = output_text

    def model_dump(self):
        return {
            "id": "resp_test",
            "output": [
                {
                    "content": [
                        {
                            "type": "output_text",
                            "text": self.output_text,
                        }
                    ]
                }
            ],
        }


class FakeResponses:
    def __init__(self, output_text):
        self.output_text = output_text
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResponse(self.output_text)


class FakeClient:
    def __init__(self, output_text):
        self.responses = FakeResponses(output_text)


class ImageOcrTests(unittest.TestCase):
    def make_image(self, width, height):
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp.close()
        Image.new("RGB", (width, height), "white").save(tmp.name, format="JPEG")
        self.addCleanup(lambda: pathlib.Path(tmp.name).unlink(missing_ok=True))
        return tmp.name

    def test_tiling_long_screenshot_preserves_width(self):
        image_path = self.make_image(1080, 6877)

        image_data = server.prepare_openai_image_inputs(image_path)

        self.assertEqual(image_data["original_size"], {"width": 1080, "height": 6877})
        self.assertGreater(image_data["tile_count"], 1)
        self.assertEqual(image_data["tile_order"], "top-to-bottom")
        self.assertEqual(image_data["tiles"][0]["bounds"]["top"], 0)
        self.assertEqual(image_data["tiles"][-1]["bounds"]["bottom"], 6877)
        for tile in image_data["tiles"]:
            self.assertEqual(tile["size"]["width"], 1080)
            self.assertLessEqual(tile["size"]["height"], 2048)
        for previous, current in zip(image_data["tiles"], image_data["tiles"][1:]):
            self.assertLess(current["bounds"]["top"], previous["bounds"]["bottom"])
            self.assertGreater(current["bounds"]["top"], previous["bounds"]["top"])

    def test_auto_mode_routes_recipe_translation_to_strict_ocr(self):
        mode = server.choose_image_mode(
            "auto",
            "Translate this recipe to English and add to my recipes",
            "",
        )

        self.assertEqual(mode, server.IMAGE_MODE_STRICT_OCR)

    def test_auto_mode_routes_dense_tesseract_to_strict_ocr(self):
        dense_text = "\n".join(
            [
                "Title",
                "Ingredient one",
                "Ingredient two",
                "1. Prepare the dough",
            ]
        )

        mode = server.choose_image_mode("auto", "", dense_text)

        self.assertEqual(mode, server.IMAGE_MODE_STRICT_OCR)

    def test_auto_mode_routes_plain_photo_request_to_visual_analysis(self):
        mode = server.choose_image_mode("auto", "What is in this photo?", "")

        self.assertEqual(mode, server.IMAGE_MODE_VISUAL_ANALYSIS)

    def test_model_detail_uses_original_only_for_supported_models(self):
        self.assertEqual(server.get_openai_image_detail("gpt-5.5"), "original")
        self.assertEqual(server.get_openai_image_detail("gpt-5.4"), "original")
        self.assertEqual(server.get_openai_image_detail("gpt-5.4-mini"), "high")
        self.assertEqual(server.get_openai_image_detail("gpt-4o"), "high")

    def test_openai_request_uses_tiles_detail_tesseract_and_max_tokens(self):
        image_path = self.make_image(1080, 3000)
        output_text = json.dumps(
            {
                "mode": "strict_ocr",
                "source_language": "Hebrew",
                "transcription": "3. Warm the oven to 220 degrees.\n4. Roll and fill.",
                "description": "",
                "uncertain_text": [],
                "warnings": [],
            }
        )
        fake_client = FakeClient(output_text)
        originals = (
            server.get_openai_client,
            server.get_option,
            server.get_int_option,
        )
        server.get_openai_client = lambda: fake_client
        server.get_option = lambda name, default=None: (
            "gpt-5.5" if name == "image_model" else default
        )
        server.get_int_option = lambda name, default: 20000
        self.addCleanup(
            lambda: setattr(server, "get_openai_client", originals[0])
        )
        self.addCleanup(lambda: setattr(server, "get_option", originals[1]))
        self.addCleanup(lambda: setattr(server, "get_int_option", originals[2]))

        openai_ocr = server.run_openai_image_analysis(
            image_path,
            "Translate this recipe to English",
            {
                "text": "3. Warm the oven to 220 degrees.\n4. Roll and fill.",
                "error": None,
            },
            "auto",
        )

        self.assertEqual(openai_ocr["mode"], server.IMAGE_MODE_STRICT_OCR)
        self.assertIn("Transcription:", openai_ocr["text"])
        call = fake_client.responses.calls[0]
        self.assertEqual(call["model"], "gpt-5.5")
        self.assertEqual(call["max_output_tokens"], 20000)
        self.assertEqual(call["text"]["format"]["name"], "image_ocr_result")
        content = call["input"][0]["content"]
        self.assertIn("Tesseract OCR hint", content[0]["text"])
        self.assertIn("Selected image mode: strict_ocr", content[0]["text"])
        image_items = [item for item in content if item["type"] == "input_image"]
        self.assertGreater(len(image_items), 1)
        self.assertTrue(all(item["detail"] == "original" for item in image_items))

    def test_response_payload_preserves_compatibility_fields(self):
        payload = server.build_image_response_payload(
            {
                "model": "gpt-5.5",
                "text": "Mode:\nstrict_ocr\n\nTranscription:\nhello",
                "raw_text": "{\"transcription\":\"hello\"}",
                "error": None,
                "mode": "strict_ocr",
                "requested_mode": "auto",
                "detail": "original",
                "structured_output": True,
                "tesseract_hint_provided": True,
                "payload": {"id": "resp_test"},
                "image_processing": {
                    "original_size": {"width": 100, "height": 200},
                    "tile_count": 1,
                    "detail": "original",
                },
            },
            {
                "engine": "tesseract",
                "languages": "eng+heb",
                "text": "hello",
                "error": None,
            },
        )

        for key in (
            "text",
            "combined_text",
            "openai_output_text",
            "openai_raw_output_text",
            "tesseract_text",
            "ocr",
            "choices",
        ):
            self.assertIn(key, payload)
        self.assertEqual(payload["openai_mode"], "strict_ocr")
        self.assertEqual(payload["image_processing"]["detail"], "original")
        self.assertEqual(
            payload["choices"][0]["message"]["content"],
            payload["combined_text"],
        )

    def test_strict_ocr_instructions_block_translation_and_reordering(self):
        instructions = server.get_image_instructions(server.IMAGE_MODE_STRICT_OCR)

        self.assertIn("Do not translate", instructions)
        self.assertIn("Do not summarize, normalize, reorder", instructions)
        self.assertIn("step order", instructions)


if __name__ == "__main__":
    unittest.main()
