from __future__ import annotations

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

PRODUCTION_ENV_VALUES = {"production", "prod"}
PLACEHOLDER_VALUES = {
    "",
    "replace-with-a-long-random-value",
    "replace-for-private-workspace",
    "justice_gateway_secret",
    "justice_gateway_access_password",
    "justicE_gateway_secret",
    "justice_gateway_access_password",
    "changeme",
    "secret",
    "example",
    "your-secret-here",
    "your-password-here",
}


def env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.environ.get(name)
        if value not in (None, ""):
            return value
    return default


def is_production() -> bool:
    return env("FINESSA_ENV", "APP_ENV", default="development").strip().lower() in PRODUCTION_ENV_VALUES


def _normalized_placeholder_set() -> set[str]:
    return {value.lower() for value in PLACEHOLDER_VALUES}


DATABASE_PATH = Path(env("DATABASE_PATH", default="instance/finessa.db"))
if not DATABASE_PATH.is_absolute():
    DATABASE_PATH = BASE_DIR / DATABASE_PATH

SECRET_KEY = env("FINESSA_SECRET") or ""
ACCESS_PASSWORD = env("FINESSA_ACCESS_PASSWORD") or ""
HTTPS = env("FINESSA_HTTPS", "JUSTICE_GATEWAY_HTTPS", default="0") == "1"


def validate_runtime_config() -> None:
    """Enforce deploy-safe defaults for production and fail fast before the app boots."""
    if not is_production():
        return

    issues: list[str] = []
    placeholders = _normalized_placeholder_set()

    if not SECRET_KEY or SECRET_KEY.lower() in placeholders:
        issues.append("FINESSA_SECRET must be set to a non-placeholder value in production")

    if not ACCESS_PASSWORD or ACCESS_PASSWORD.lower() in placeholders:
        issues.append("FINESSA_ACCESS_PASSWORD must be set to a non-placeholder value in production")

    if len(SECRET_KEY) < 32:
        issues.append("FINESSA_SECRET should be at least 32 characters long in production")

    try:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        issues.append(f"Unable to create the database directory for {DATABASE_PATH}: {exc}")

    if HTTPS is False:
        issues.append("Production deployments should set FINESSA_HTTPS=1 behind TLS termination or a reverse proxy")

    if issues:
        raise RuntimeError("Production configuration validation failed: " + "; ".join(issues))


# Local development defaults: generated secrets allowed, but production must opt in via FINESSA_ENV=production.
if not SECRET_KEY:
    SECRET_KEY = secrets.token_hex(32)

if not ACCESS_PASSWORD and not is_production():
    ACCESS_PASSWORD = ""
