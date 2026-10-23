"""Validated avatar configuration. Never accept a replacement face from client settings."""
from __future__ import annotations
from dataclasses import dataclass

IDENTITY_ID = "finessa-original"
MASTER_IMAGE = "static/img/finessa-presenter.webp"
ALLOWED = {
    "wardrobe": ("executive",),
    "hairstyle": ("original",),
    "environment": ("studio",),
    "specialty": ("justice",),
}

@dataclass(frozen=True)
class AvatarConfig:
    identity_id: str = IDENTITY_ID
    master_image: str = MASTER_IMAGE
    wardrobe: str = "executive"
    hairstyle: str = "original"
    environment: str = "studio"
    specialty: str = "justice"

def validate_config(settings: dict | None = None) -> AvatarConfig:
    settings = settings or {}
    if not isinstance(settings, dict):
        raise ValueError("Avatar settings must be an object")
    unknown = set(settings) - set(ALLOWED)
    if unknown:
        raise ValueError("Unsupported avatar setting: " + ", ".join(sorted(unknown)))
    for field, choices in ALLOWED.items():
        if settings.get(field, choices[0]) not in choices:
            raise ValueError("Unsupported value for " + field)
    return AvatarConfig(**settings)
