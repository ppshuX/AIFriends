# Security Config Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove runnable public signing secrets, require explicit independent Django/JWT secrets, centralize refresh-cookie security, and document a reproducible secure setup.

**Architecture:** Keep the existing single Django settings module. Add one small environment parsing module used by settings, plus one account-cookie helper used by the four authentication endpoints. Validate behavior with standard-library and Django tests before changing production code.

**Tech Stack:** Python 3.12, Django 6.0.1, Django REST Framework, SimpleJWT, python-dotenv, unittest/Django test runner.

## Global Constraints

- Keep the existing Django/Vue architecture and API paths.
- `DJANGO_SECRET_KEY` and `JWT_SIGNING_KEY` are mandatory, independent, and at least 50 characters.
- `DJANGO_DEBUG` defaults to `false`; no runnable secret fallback is committed.
- AI, ASR, TTS, LanceDB, dependency upgrades, deployment, push, and production data are out of scope.
- Every behavior change follows red-green TDD and ends in an independently reviewable commit.

---

### Execution preflight: Isolated Python environment

Create the task environment outside the repository so dependency installation does not alter tracked or untracked workspace files:

```powershell
$securityVenv = Join-Path $env:LOCALAPPDATA 'Codex\venvs\AIFriends-security-config'
python -m venv $securityVenv
& "$securityVenv\Scripts\python.exe" -m pip install --upgrade pip
& "$securityVenv\Scripts\python.exe" -m pip install -r backend\requirements.txt
```

Use `$securityVenv\Scripts\python.exe` in the commands below when the documented `.venv` path is not present. Verify the baseline by running the existing Django test command with temporary valid secrets; because the repository initially has no real tests, record the discovered test count instead of treating exit code alone as coverage.

---

### Task 1: Strict environment configuration

**Files:**
- Create: `backend/backend/env.py`
- Create: `backend/backend/tests/__init__.py`
- Create: `backend/backend/tests/test_env.py`
- Create: `backend/backend/tests/test_settings.py`
- Modify: `backend/backend/settings.py`

**Interfaces:**
- Produces: `get_bool(name: str, default: bool = False) -> bool`
- Produces: `get_csv(name: str, default: tuple[str, ...] = ()) -> list[str]`
- Produces: `get_required_secret(name: str) -> str`
- Consumes: process environment and `backend/.env`

- [ ] **Step 1: Write failing unit tests for environment parsing**

```python
import os
from unittest import TestCase
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured

from backend.env import get_bool, get_csv, get_required_secret


class EnvironmentParsingTests(TestCase):
    def test_get_bool_accepts_supported_values(self):
        for raw, expected in {
            "true": True, "1": True, "yes": True, "on": True,
            "false": False, "0": False, "no": False, "off": False,
        }.items():
            with self.subTest(raw=raw), patch.dict(os.environ, {"FLAG": raw}, clear=False):
                self.assertIs(get_bool("FLAG"), expected)

    def test_get_bool_rejects_unknown_value(self):
        with patch.dict(os.environ, {"FLAG": "sometimes"}, clear=False):
            with self.assertRaisesRegex(ImproperlyConfigured, "FLAG"):
                get_bool("FLAG")

    def test_get_csv_strips_whitespace_and_empty_items(self):
        with patch.dict(os.environ, {"HOSTS": "localhost, example.com, ,"}, clear=False):
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
```

- [ ] **Step 2: Run parser tests and verify RED**

Run from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m unittest backend.tests.test_env -v
```

Expected: import failure because `backend.env` does not exist.

- [ ] **Step 3: Implement the minimal parser module**

```python
import os

from django.core.exceptions import ImproperlyConfigured


TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}
PLACEHOLDER_SECRETS = {
    "replace-with-generated-secret",
    "replace-with-independent-generated-secret",
}


def get_bool(name, default=False):
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    value = raw_value.strip().lower()
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    raise ImproperlyConfigured(f"{name} must be a boolean value")


def get_csv(name, default=()):
    raw_value = os.getenv(name)
    if raw_value is None:
        return list(default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def get_required_secret(name):
    value = os.getenv(name, "").strip()
    if len(value) < 50 or value in PLACEHOLDER_SECRETS:
        raise ImproperlyConfigured(
            f"{name} must be set to an independently generated secret of at least 50 characters"
        )
    return value
```

- [ ] **Step 4: Run parser tests and verify GREEN**

Run the command from Step 2. Expected: 5 tests pass.

- [ ] **Step 5: Write failing subprocess tests for Django settings**

```python
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
        result = run_settings({
            "DJANGO_SECRET_KEY": VALID_DJANGO_SECRET,
            "JWT_SIGNING_KEY": VALID_JWT_SECRET,
            "DJANGO_DEBUG": "true",
            "DJANGO_ALLOWED_HOSTS": "localhost,example.com",
            "DJANGO_CORS_ALLOWED_ORIGINS": "http://localhost:5173,https://example.com",
        })
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout.strip())
        self.assertEqual(data["secret"], VALID_DJANGO_SECRET)
        self.assertEqual(data["jwt"], VALID_JWT_SECRET)
        self.assertIs(data["debug"], True)
        self.assertEqual(data["hosts"], ["localhost", "example.com"])
        self.assertEqual(data["cors"], ["http://localhost:5173", "https://example.com"])

    def test_settings_reject_missing_secrets(self):
        result = run_settings({})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", result.stderr)

    def test_settings_reject_matching_secrets(self):
        result = run_settings({
            "DJANGO_SECRET_KEY": VALID_DJANGO_SECRET,
            "JWT_SIGNING_KEY": VALID_DJANGO_SECRET,
        })
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be different", result.stderr)
```

- [ ] **Step 6: Run settings tests and verify RED**

```powershell
.\.venv\Scripts\python.exe -m unittest backend.tests.test_settings -v
```

Expected: failures because settings ignore the new variables and do not define an independent signing key.

- [ ] **Step 7: Wire strict environment values into settings**

Move `load_dotenv()` after `BASE_DIR`, call `load_dotenv(BASE_DIR / ".env")`, import the three helpers, and replace the hardcoded values with:

```python
from django.core.exceptions import ImproperlyConfigured

SECRET_KEY = get_required_secret("DJANGO_SECRET_KEY")
JWT_SIGNING_KEY = get_required_secret("JWT_SIGNING_KEY")
if SECRET_KEY == JWT_SIGNING_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY and JWT_SIGNING_KEY must be different")

DEBUG = get_bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = get_csv("DJANGO_ALLOWED_HOSTS", default=("127.0.0.1", "localhost"))
```

Set CORS and SimpleJWT with:

```python
CORS_ALLOWED_ORIGINS = get_csv("DJANGO_CORS_ALLOWED_ORIGINS")
SIMPLE_JWT["SIGNING_KEY"] = JWT_SIGNING_KEY
```

- [ ] **Step 8: Run both environment test modules and verify GREEN**

```powershell
.\.venv\Scripts\python.exe -m unittest backend.tests.test_env backend.tests.test_settings -v
```

Expected: 8 tests pass.

- [ ] **Step 9: Commit strict settings behavior**

```powershell
git add backend/backend/env.py backend/backend/settings.py backend/backend/tests
git commit -m "security: require independent signing secrets"
```

---

### Task 2: Centralized refresh-cookie policy

**Files:**
- Create: `backend/web/views/user/account/cookies.py`
- Create: `backend/backend/tests/test_refresh_cookie.py`
- Modify: `backend/web/views/user/account/login.py`
- Modify: `backend/web/views/user/account/register.py`
- Modify: `backend/web/views/user/account/refresh_token.py`
- Modify: `backend/web/views/user/account/logout.py`

**Interfaces:**
- Consumes: Django `settings.DEBUG` and a response implementing `set_cookie`/`delete_cookie`
- Produces: `set_refresh_token_cookie(response, token) -> None`
- Produces: `delete_refresh_token_cookie(response) -> None`

- [ ] **Step 1: Write failing cookie-policy tests**

```python
from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings

from web.views.user.account.cookies import (
    delete_refresh_token_cookie,
    set_refresh_token_cookie,
)


class RefreshTokenCookieTests(SimpleTestCase):
    @override_settings(DEBUG=True)
    def test_development_cookie_is_not_secure(self):
        response = HttpResponse()
        set_refresh_token_cookie(response, "token")
        cookie = response.cookies["refresh_token"]
        self.assertFalse(cookie["secure"])
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertEqual(cookie["path"], "/")

    @override_settings(DEBUG=False)
    def test_production_cookie_is_secure(self):
        response = HttpResponse()
        set_refresh_token_cookie(response, "token")
        self.assertTrue(response.cookies["refresh_token"]["secure"])

    @override_settings(DEBUG=False)
    def test_delete_cookie_uses_same_security_attributes(self):
        response = HttpResponse()
        delete_refresh_token_cookie(response)
        cookie = response.cookies["refresh_token"]
        self.assertEqual(cookie["max-age"], 0)
        self.assertTrue(cookie["secure"])
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertEqual(cookie["path"], "/")
```

- [ ] **Step 2: Run cookie tests and verify RED**

Run from `backend/` with valid test secrets:

```powershell
$env:DJANGO_SECRET_KEY='django-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'; $env:JWT_SIGNING_KEY='jwt-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'; .\.venv\Scripts\python.exe manage.py test backend.tests.test_refresh_cookie -v 2
```

Expected: import failure because `cookies.py` does not exist.

- [ ] **Step 3: Implement cookie helpers**

```python
from django.conf import settings


REFRESH_TOKEN_COOKIE = "refresh_token"
REFRESH_TOKEN_MAX_AGE = 7 * 24 * 60 * 60


def cookie_options():
    return {
        "httponly": True,
        "samesite": "Lax",
        "secure": not settings.DEBUG,
        "path": "/",
    }


def set_refresh_token_cookie(response, token):
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=str(token),
        max_age=REFRESH_TOKEN_MAX_AGE,
        **cookie_options(),
    )


def delete_refresh_token_cookie(response):
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE,
        samesite="Lax",
        secure=not settings.DEBUG,
        path="/",
    )
```

- [ ] **Step 4: Replace duplicated cookie operations in account views**

Import and call `set_refresh_token_cookie` from login, register, and refresh-token views. Import and call `delete_refresh_token_cookie` from logout. Remove all duplicated literal cookie options.

- [ ] **Step 5: Run cookie tests and verify GREEN**

Run the command from Step 2. Expected: 3 tests pass.

- [ ] **Step 6: Run all security tests**

```powershell
$env:DJANGO_SECRET_KEY='django-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'; $env:JWT_SIGNING_KEY='jwt-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'; .\.venv\Scripts\python.exe manage.py test backend.tests -v 2
```

Expected: all environment, settings, and cookie tests pass.

- [ ] **Step 7: Commit centralized cookie behavior**

```powershell
git add backend/web/views/user/account backend/backend/tests/test_refresh_cookie.py
git commit -m "security: centralize refresh cookie policy"
```

---

### Task 3: Secure setup documentation

**Files:**
- Create: `backend/.env.example`
- Modify: `README.md`

**Interfaces:**
- Documents: exact environment names consumed by Task 1
- Documents: local secret generation and startup procedure

- [ ] **Step 1: Add a non-runnable environment template**

```dotenv
# Generate each value separately with:
# python -c "import secrets; print(secrets.token_urlsafe(64))"
DJANGO_SECRET_KEY=replace-with-generated-secret
JWT_SIGNING_KEY=replace-with-independent-generated-secret

DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# AI features are configured separately and remain optional for basic startup.
API_KEY=
API_BASE=
WSS_URL=
VOICE_URL=
```

- [ ] **Step 2: Update README setup instructions**

Change Python 3.8+ to Python 3.12+, replace manual package installation with `pip install -r requirements.txt`, and insert the following sequence before migrations:

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Explain that the command must run twice and its two different outputs replace the placeholders. Add the POSIX equivalent `cp .env.example .env`. State that production must generate new values, set `DJANGO_DEBUG=false`, and configure its public host/origin without committing `.env`.

- [ ] **Step 3: Verify documentation matches settings**

Run from repository root:

```powershell
$required=@('DJANGO_SECRET_KEY','JWT_SIGNING_KEY','DJANGO_DEBUG','DJANGO_ALLOWED_HOSTS','DJANGO_CORS_ALLOWED_ORIGINS'); foreach($name in $required){ if(-not (Select-String -LiteralPath backend/.env.example,README.md -Pattern $name -Quiet)){ throw "Missing documentation for $name" } }
```

Expected: exit 0.

- [ ] **Step 4: Commit setup documentation**

```powershell
git add backend/.env.example README.md
git commit -m "docs: add secure environment setup"
```

---

### Task 4: Full verification and security scan

**Files:**
- Verify only; modify earlier task files only if a check exposes a defect.

**Interfaces:**
- Consumes: completed Tasks 1-3
- Produces: command evidence for completion

- [ ] **Step 1: Run complete Django tests**

```powershell
$env:DJANGO_SECRET_KEY='django-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'; $env:JWT_SIGNING_KEY='jwt-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'; .\backend\.venv\Scripts\python.exe backend\manage.py test -v 2
```

Expected: all discovered tests pass with zero failures.

- [ ] **Step 2: Run Django configuration checks**

```powershell
$env:DJANGO_SECRET_KEY='django-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'; $env:JWT_SIGNING_KEY='jwt-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'; .\backend\.venv\Scripts\python.exe backend\manage.py check
.\backend\.venv\Scripts\python.exe backend\manage.py makemigrations --check --dry-run
.\backend\.venv\Scripts\python.exe backend\manage.py check --deploy
```

Expected: normal check and migration drift check pass. Deployment check may report remaining out-of-scope hardening warnings; record them exactly instead of claiming a clean deployment check.

- [ ] **Step 3: Run syntax, diff, and secret scans**

```powershell
@'
import ast
from pathlib import Path
for path in Path('backend').rglob('*.py'):
    ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
print('Python syntax OK')
'@ | .\backend\.venv\Scripts\python.exe -
git diff --check HEAD~3..HEAD
git grep -n "django-insecure-" -- ':!docs/superpowers/**'
git status --short --branch
```

Expected: syntax and diff checks pass, secret grep returns no tracked runtime match, and the worktree is clean.

- [ ] **Step 4: Review commit boundaries**

```powershell
git log --oneline --decorate -5
git diff --stat master...HEAD
```

Expected: one design commit, one plan commit, and three implementation/documentation commits, all limited to the approved scope.
