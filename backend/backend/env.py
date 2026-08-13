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
            f"{name} must be set to an independently generated secret "
            "of at least 50 characters"
        )
    return value
