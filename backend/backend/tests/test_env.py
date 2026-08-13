import os
from unittest import TestCase
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured

from backend.env import get_bool, get_csv, get_required_secret


class EnvironmentParsingTests(TestCase):
    def test_get_bool_accepts_supported_values(self):
        for raw, expected in {
            "true": True,
            "1": True,
            "yes": True,
            "on": True,
            "false": False,
            "0": False,
            "no": False,
            "off": False,
        }.items():
            with self.subTest(raw=raw), patch.dict(
                os.environ, {"FLAG": raw}, clear=False
            ):
                self.assertIs(get_bool("FLAG"), expected)

    def test_get_bool_rejects_unknown_value(self):
        with patch.dict(os.environ, {"FLAG": "sometimes"}, clear=False):
            with self.assertRaisesRegex(ImproperlyConfigured, "FLAG"):
                get_bool("FLAG")

    def test_get_csv_strips_whitespace_and_empty_items(self):
        with patch.dict(
            os.environ, {"HOSTS": "localhost, example.com, ,"}, clear=False
        ):
            self.assertEqual(get_csv("HOSTS"), ["localhost", "example.com"])

    def test_get_required_secret_rejects_missing_short_and_placeholder_values(self):
        for value in (None, "short", "replace-with-generated-secret"):
            env = {} if value is None else {"SECRET": value}
            with self.subTest(value=value), patch.dict(os.environ, env, clear=True):
                with self.assertRaisesRegex(ImproperlyConfigured, "SECRET"):
                    get_required_secret("SECRET")

    def test_get_required_secret_returns_long_secret(self):
        value = "a" * 64
        with patch.dict(os.environ, {"SECRET": value}, clear=True):
            self.assertEqual(get_required_secret("SECRET"), value)
