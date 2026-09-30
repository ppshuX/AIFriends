"""读写数据目录 .env 里的大模型配置。

便携包与本地开发共用 backend.settings.DATA_DIR（由 AIFRIENDS_DATA_DIR 或
run_server.py 决定）。只向调用方报告密钥是否已配置，绝不回传密钥本身。
"""

import os
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_API_BASE = "https://tokenhub.tencentmaas.com/v1"
_MAX_KEY_LEN = 512
_MAX_BASE_LEN = 300
_KEY_FORBIDDEN = set(" \t\"'`#\\")


def api_key_configured():
    return bool(os.getenv("API_KEY", "").strip())


def env_file_path():
    from django.conf import settings

    return Path(settings.DATA_DIR) / ".env"


def validate_api_key(raw):
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("API Key 不能为空")
    value = raw.strip()
    if (
        len(value) < 8
        or len(value) > _MAX_KEY_LEN
        or any(ch in _KEY_FORBIDDEN or ord(ch) < 33 or ord(ch) > 126 for ch in value)
    ):
        raise ValueError("API Key 格式不正确")
    return value


def validate_api_base(raw):
    if not isinstance(raw, str):
        raise ValueError("API Base 地址不正确")
    value = raw.strip()
    if not value or len(value) > _MAX_BASE_LEN:
        raise ValueError("API Base 地址不正确")
    if any(ch.isspace() or ord(ch) < 33 for ch in value):
        raise ValueError("API Base 地址不正确")
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("API Base 地址不正确")
    return value.rstrip("/")


def upsert_env_file(path, updates):
    """替换或追加 KEY=value。其余行（含其他密钥）原样保留。UTF-8 无 BOM。"""
    path = Path(path)
    original = ""
    if path.exists():
        original = path.read_text(encoding="utf-8-sig")
    lines = original.splitlines()
    remaining = dict(updates)
    new_lines = []
    for line in lines:
        name, sep, _value = line.partition("=")
        if sep and name in remaining and name.replace("_", "").isalnum():
            new_lines.append(f"{name}={remaining.pop(name)}")
        else:
            new_lines.append(line)
    for name, value in remaining.items():
        new_lines.append(f"{name}={value}")
    text = "\n".join(new_lines)
    if not text.endswith("\n"):
        text += "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def save_llm_config(api_key, api_base=None):
    key = validate_api_key(api_key)
    updates = {"API_KEY": key}
    if api_base is not None and str(api_base).strip():
        updates["API_BASE"] = validate_api_base(str(api_base))
    elif not os.getenv("API_BASE", "").strip():
        updates["API_BASE"] = DEFAULT_API_BASE
    upsert_env_file(env_file_path(), updates)
    os.environ["API_KEY"] = updates["API_KEY"]
    if "API_BASE" in updates:
        os.environ["API_BASE"] = updates["API_BASE"]
