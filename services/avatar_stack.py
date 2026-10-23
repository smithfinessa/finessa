from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None

try:
    from insightface.app import FaceAnalysis  # type: ignore
except Exception:  # pragma: no cover
    FaceAnalysis = None


BASE_DIR = Path(__file__).resolve().parent.parent
AVATAR_DIR = BASE_DIR / "storage" / "avatar"


def _ensure_avatar_dir() -> Path:
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    return AVATAR_DIR


def _command_available(cmd: str) -> bool:
    return subprocess.run(["sh", "-lc", f"command -v {cmd} >/dev/null 2>&1"], capture_output=True).returncode == 0


def avatar_status() -> dict:
    status = {
        "face_detection": "unavailable",
        "face_recognition": "unavailable",
        "local_llm": "unavailable",
        "tts": "unavailable",
        "sadtalker": "unavailable",
        "avatar_mode": os.environ.get("FINESSA_AVATAR_MODE", "local_free"),
    }

    if cv2 is not None:
        status["face_detection"] = "opencv"
    if FaceAnalysis is not None:
        status["face_recognition"] = "insightface"
    if _command_available("ollama"):
        status["local_llm"] = "ollama"
    if _command_available("piper") or _command_available("espeak"):
        status["tts"] = "piper" if _command_available("piper") else "espeak"
    if os.environ.get("FINESSA_SADTALKER_HOME"):
        status["sadtalker"] = "configured"

    return status


def _reference_embedding() -> list[float] | None:
    ref_path = os.environ.get("FINESSA_AVATAR_REF_IMAGE")
    if not ref_path or FaceAnalysis is None or cv2 is None:
        return None
    p = Path(ref_path)
    if not p.exists():
        return None
    app = FaceAnalysis(name="buffalov")
    app.prepare(ctx_id=0, det_size=(640, 640))
    img = cv2.imread(str(p))
    if img is None:
        return None
    faces = app.get(img)
    if not faces:
        return None
    return faces[0].embedding.tolist()


def verify_face_image(image_path: str | Path) -> dict:
    if FaceAnalysis is None or cv2 is None:
        return {"ok": False, "reason": "InsightFace/Opencv is not installed."}

    app = FaceAnalysis(name="buffalov")
    app.prepare(ctx_id=0, det_size=(640, 640))
    image = Path(image_path)
    if not image.exists():
        return {"ok": False, "reason": "Face image was not found."}

    frame = cv2.imread(str(image))
    if frame is None:
        return {"ok": False, "reason": "Could not decode the supplied image."}

    faces = app.get(frame)
    if not faces:
        return {"ok": False, "reason": "No face detected in the supplied image."}

    ref_embedding = _reference_embedding()
    if ref_embedding is None:
        return {
            "ok": False,
            "verified": False,
            "reason": "Identity cannot be verified without a configured, readable reference image.",
            "face_count": len(faces),
        }

    candidate = faces[0].embedding
    marker = sum((a - b) ** 2 for a, b in zip(candidate, ref_embedding)) ** 0.5
    threshold = float(os.environ.get("FINESSA_AVATAR_MATCH_THRESHOLD", "0.5"))
    ok = marker <= threshold

    return {
        "ok": ok,
        "verified": ok,
        "reason": "Face matched configured reference." if ok else f"Face distance {marker:.4f} exceeded threshold {threshold:.4f}.",
        "distance": round(float(marker), 4),
        "face_count": len(faces),
    }


def decode_base64_image(raw_data: str) -> str:
    if not raw_data:
        raise ValueError("No image data provided.")
    data = raw_data.split(",", 1)[-1]
    decoded = base64.b64decode(data)
    target = _ensure_avatar_dir() / f"capture_{hashlib.sha256(decoded).hexdigest()[:12]}.png"
    target.write_bytes(decoded)
    return str(target)


def ollama_chat(prompt: str, model: str | None = None) -> str:
    if not _command_available("ollama"):
        raise RuntimeError("Ollama is not installed or not on PATH.")

    chosen_model = model or os.environ.get("FINESSA_OLLAMA_MODEL", "llama3.1")
    result = subprocess.run(
        ["ollama", "run", chosen_model],
        input=prompt,
        text=True,
        capture_output=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Ollama call failed.")
    return (result.stdout or "").strip()


def generate_local_tts(text: str, output_path: str | Path | None = None) -> str:
    out = Path(output_path) if output_path else _ensure_avatar_dir() / f"tts_{hashlib.sha256(text.encode()).hexdigest()[:12]}.wav"
    if _command_available("piper"):
        model = os.environ.get("FINESSA_PIPER_MODEL", "")
        cmd = ["piper", "--output_file", str(out)]
        if model:
            cmd = ["piper", "--model", model, "--output_file", str(out)]
        proc = subprocess.run(cmd, input=text, text=True, capture_output=True)
        if proc.returncode == 0 and out.exists():
            return str(out)
    if _command_available("espeak"):
        proc = subprocess.run(["espeak", "-w", str(out), text], capture_output=True, text=True)
        if proc.returncode == 0 and out.exists():
            return str(out)
    raise RuntimeError("No local TTS engine (piper or espeak) is configured.")


def sadtalker_infer(audio_path: str | Path, image_path: str | Path, result_dir: str | Path | None = None) -> str:
    sadtalker_home = os.environ.get("FINESSA_SADTALKER_HOME")
    if not sadtalker_home:
        raise RuntimeError("FINESSA_SADTALKER_HOME is not configured.")

    work_dir = Path(result_dir) if result_dir else _ensure_avatar_dir() / "results"
    work_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "python",
        str(Path(sadtalker_home) / "inference.py"),
        "--driven_audio",
        str(audio_path),
        "--source_image",
        str(image_path),
        "--result_dir",
        str(work_dir),
        "--still",
        "--preprocess",
        "full",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "SadTalker inference failed.")
    return str(work_dir)


__all__ = [
    "avatar_status",
    "verify_face_image",
    "decode_base64_image",
    "ollama_chat",
    "generate_local_tts",
    "sadtalker_infer",
]
