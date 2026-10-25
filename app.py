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

SECRET_KEY = env("FINESSA_SECRET") or ""
ACCESS_PASSWORD = env("FINESSA_ACCESS_PASSWORD") or ""
HTTPS = env("FINESSA_HTTPS", "JUSTICE_GATEWAY_HTTPS", default="0") == "1"

PRODUCTION_ENV_VALUES = {"production", "prod"}
PLACEHOLDER_VALUES = {
    "",
    "replace-with-a-long-random-value",
    "replace-for-private-workspace",
    "justice_gateway_secret",
    "justice_gateway_access_password",
    "JUSTICE_GATEWAY_SECRET",
    "JUSTICE_GATEWAY_ACCESS_PASSWORD",
    "changeme",
    "secret",
}


def is_production() -> bool:
    return env("FINESSA_ENV", "APP_ENV", default="development").lower() in PRODUCTION_ENV_VALUES


def validate_runtime_config() -> None:
    if not is_production():
        return

    issues: list[str] = []

    if not SECRET_KEY or SECRET_KEY.lower() in {p.lower() for p in PLACEHOLDER_VALUES}:
        issues.append("FINESSA_SECRET must be set to a non-placeholder value in production")

    if not ACCESS_PASSWORD or ACCESS_PASSWORD.lower() in {p.lower() for p in PLACEHOLDER_VALUES}:
        issues.append("FINESSA_ACCESS_PASSWORD must be set to a non-placeholder value in production")

    try:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        issues.append(f"Unable to create database directory for {DATABASE_PATH}: {exc}")

    if issues:
        raise RuntimeError("Production configuration validation failed: " + "; ".join(issues))


# Backward-compatible defaults for local development; production must opt in via FINESSA_ENV=production.
if not SECRET_KEY:
    SECRET_KEY = secrets.token_hex(32)

if not ACCESS_PASSWORD and not is_production():
    ACCESS_PASSWORD = ""
