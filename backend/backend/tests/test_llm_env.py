import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from web.utils.llm_env import upsert_env_file, validate_api_base, validate_api_key
from web.views.config.llm import LlmConfigView
from web.views.friend.message.chat.chat import MessageChatView


def _user():
    user = Mock()
    user.is_authenticated = True
    user.pk = 1
    user.id = 1
    return user


class LlmEnvFileTests(SimpleTestCase):
    def test_upsert_replaces_api_key_and_keeps_other_secrets(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text(
                "DJANGO_SECRET_KEY=keep-this-secret\nAPI_KEY=\n# comment\n",
                encoding="utf-8",
            )
            upsert_env_file(path, {"API_KEY": "sk-local-test-key"})
            raw = path.read_bytes()
            self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
            text = raw.decode("utf-8")
            self.assertIn("DJANGO_SECRET_KEY=keep-this-secret\n", text)
            self.assertIn("API_KEY=sk-local-test-key\n", text)
            self.assertIn("# comment\n", text)
            self.assertEqual(text.count("API_KEY="), 1)

    def test_validate_rejects_injection_and_accepts_normal_key(self):
        self.assertEqual(validate_api_key("  sk-normal-key  "), "sk-normal-key")
        with self.assertRaises(ValueError):
            validate_api_key("short")
        with self.assertRaises(ValueError):
            validate_api_key("sk-bad\nAPI_KEY=injected")
        with self.assertRaises(ValueError):
            validate_api_key("")
        self.assertEqual(
            validate_api_base("https://tokenhub.tencentmaas.com/v1/"),
            "https://tokenhub.tencentmaas.com/v1",
        )
        with self.assertRaises(ValueError):
            validate_api_base("file:///tmp/x")


class LlmConfigViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self._old_key = os.environ.get("API_KEY")
        self._old_base = os.environ.get("API_BASE")
        os.environ.pop("API_KEY", None)
        os.environ.pop("API_BASE", None)

    def tearDown(self):
        if self._old_key is None:
            os.environ.pop("API_KEY", None)
        else:
            os.environ["API_KEY"] = self._old_key
        if self._old_base is None:
            os.environ.pop("API_BASE", None)
        else:
            os.environ["API_BASE"] = self._old_base

    def test_get_reports_boolean_only(self):
        os.environ["API_KEY"] = "sk-should-not-leak"
        request = self.factory.get("/api/config/llm/")
        force_authenticate(request, user=_user())
        response = LlmConfigView.as_view()(request)
        payload = json.dumps(response.data, ensure_ascii=False)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["api_key_configured"])
        self.assertNotIn("sk-should-not-leak", payload)
        self.assertNotIn("api_key", payload.replace("api_key_configured", ""))

    def test_post_writes_env_and_process_without_returning_key(self):
        with TemporaryDirectory() as tmp:
            with override_settings(DATA_DIR=Path(tmp)):
                request = self.factory.post(
                    "/api/config/llm/",
                    {"api_key": "sk-local-test-key", "api_base": ""},
                    format="json",
                    REMOTE_ADDR="127.0.0.1",
                )
                force_authenticate(request, user=_user())
                response = LlmConfigView.as_view()(request)
                payload = json.dumps(response.data, ensure_ascii=False)
                self.assertEqual(response.status_code, 200, response.data)
                self.assertTrue(response.data["api_key_configured"])
                self.assertNotIn("sk-local-test-key", payload)
                self.assertEqual(os.environ["API_KEY"], "sk-local-test-key")
                self.assertEqual(
                    os.environ["API_BASE"],
                    "https://tokenhub.tencentmaas.com/v1",
                )
                text = (Path(tmp) / ".env").read_text(encoding="utf-8")
                self.assertIn("API_KEY=sk-local-test-key\n", text)
                self.assertIn(
                    "API_BASE=https://tokenhub.tencentmaas.com/v1\n",
                    text,
                )

    def test_post_rejects_remote_clients(self):
        with TemporaryDirectory() as tmp:
            with override_settings(DATA_DIR=Path(tmp)):
                request = self.factory.post(
                    "/api/config/llm/",
                    {"api_key": "sk-local-test-key"},
                    format="json",
                    REMOTE_ADDR="203.0.113.8",
                )
                force_authenticate(request, user=_user())
                response = LlmConfigView.as_view()(request)
                self.assertEqual(response.status_code, 403)
                self.assertFalse((Path(tmp) / ".env").exists())
                self.assertNotIn("API_KEY", os.environ)

    def test_chat_rejects_missing_key_before_streaming(self):
        request = self.factory.post(
            "/api/friend/message/chat/",
            {"friend_id": 1, "message": "你好"},
            format="json",
        )
        force_authenticate(request, user=_user())
        response = MessageChatView.as_view()(request)
        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content.decode("utf-8"))
        self.assertEqual(body["code"], "api_key_missing")
        self.assertNotIn("api_key", body)
