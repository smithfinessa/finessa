from __future__ import annotations
import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.environ.get(name)
        if value not in (None, ""):
            return value
    return default


DATABASE_PATH = Path(env("DATABASE_PATH", default="instance/finessa.db"))
if not DATABASE_PATH.is_absolute():
    DATABASE_PATH = BASE_DIR / DATABASE_PATH

# Do not ship weak default secrets. Require explicit configuration in production,
# but allow a generated key for local development and tests.
SECRET_KEY = env("FINESSA_SECRET") or secrets.token_hex(32)
ACCESS_PASSWORD = env("FINESSA_ACCESS_PASSWORD") or ""
HTTPS = env("FINESSA_HTTPS", "JUSTICE_GATEWAY_HTTPS", default="0") == "1"
