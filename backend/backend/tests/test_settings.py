import json
import os
import subprocess
import sys
from pathlib import Path
from unittest import TestCase


BACKEND_DIR = Path(__file__).resolve().parents[2]
VALID_DJANGO_SECRET = "django-" + "a" * 64
VALID_JWT_SECRET = "jwt-" + "b" * 64


def run_settings(extra_env):
    env = os.environ.copy()
    for name in ("DJANGO_SECRET_KEY", "JWT_SIGNING_KEY"):
        env.pop(name, None)
    env.update(extra_env)
    code = """
import json
import dotenv

dotenv.load_dotenv = lambda *args, **kwargs: False
from backend import settings
print(json.dumps({
    'secret': settings.SECRET_KEY,
    'jwt': settings.SIMPLE_JWT['SIGNING_KEY'],
    'debug': settings.DEBUG,
    'hosts': settings.ALLOWED_HOSTS,
    'cors': settings.CORS_ALLOWED_ORIGINS,
}))
"""
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=BACKEND_DIR,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


class SettingsEnvironmentTests(TestCase):
    def test_settings_use_independent_environment_secrets_and_lists(self):
        result = run_settings(
            {
                "DJANGO_SECRET_KEY": VALID_DJANGO_SECRET,
                "JWT_SIGNING_KEY": VALID_JWT_SECRET,
                "DJANGO_DEBUG": "true",
                "DJANGO_ALLOWED_HOSTS": "localhost,example.com",
                "DJANGO_CORS_ALLOWED_ORIGINS": (
                    "http://localhost:5173,https://example.com"
                ),
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout.strip())
        self.assertEqual(data["secret"], VALID_DJANGO_SECRET)
        self.assertEqual(data["jwt"], VALID_JWT_SECRET)
        self.assertIs(data["debug"], True)
        self.assertEqual(data["hosts"], ["localhost", "example.com"])
        self.assertEqual(
            data["cors"], ["http://localhost:5173", "https://example.com"]
        )

    def test_settings_reject_missing_secrets(self):
        result = run_settings({})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", result.stderr)

    def test_settings_reject_matching_secrets(self):
        result = run_settings(
            {
                "DJANGO_SECRET_KEY": VALID_DJANGO_SECRET,
                "JWT_SIGNING_KEY": VALID_DJANGO_SECRET,
            }
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be different", result.stderr)
