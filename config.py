from __future__ import annotations
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.environ.get(name)
        if value not in (None, ""):
            return value
    return default

DATABASE_PATH = Path(env("DATABASE_PATH", default="instance/finessa.db"))
if not DATABASE_PATH.is_absolute():
    DATABASE_PATH = BASE_DIR / DATABASE_PATH
SECRET_KEY = env("FINESSA_SECRET", "JUSTICE_GATEWAY_SECRET")
ACCESS_PASSWORD = env("FINESSA_ACCESS_PASSWORD", "JUSTICE_GATEWAY_ACCESS_PASSWORD")
HTTPS = env("FINESSA_HTTPS", "JUSTICE_GATEWAY_HTTPS", default="0") == "1"
