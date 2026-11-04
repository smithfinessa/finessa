"""Hybrid conversational inference. Standard-library HTTP, explicit cloud opt-in.

No case workspace content is sent to models by this module. Callers must pass
only user-approved conversation text and must apply compliance checks first.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

SYSTEM_PROMPT = (
    "You are Finessa, a clearly identified digital AI information assistant. "
    "Help with general knowledge, academic research and legal information. "
    "Do not claim to be a human or a licensed attorney. Do not invent sources, "
    "citations, court holdings, or current legal status. When legal sources are "
    "not independently verified, state that clearly. Distinguish allegations "
    "from established facts. Be concise and explain uncertainty."
)
MAX_MESSAGE = 4000
MAX_HISTORY = 12


@dataclass(frozen=True)
class InferenceResult:
    answer: str
    provider: str
    model: str


class InferenceUnavailable(RuntimeError):
    pass


def _endpoint(env: dict, prefix: str, default: str) -> str:
    url = env.get(prefix + "_URL", default).rstrip("/")
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise InferenceUnavailable("Invalid model endpoint URL")
    if prefix == "FINESSA_CLOUD" and parsed.scheme != "https":
        raise InferenceUnavailable("Cloud endpoint must use HTTPS")
    return url


def _messages(message: str, history: list | None) -> list[dict]:
    if not isinstance(message, str) or not message.strip() or len(message) > MAX_MESSAGE:
        raise ValueError("Message must be 1-4000 characters")
    result = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in (history or [])[-MAX_HISTORY:]:
        if not isinstance(item, dict):
            continue
        role, content = item.get("role"), item.get("content")
        if role in ("user", "assistant") and isinstance(content, str) and 0 < len(content) <= MAX_MESSAGE:
            result.append({"role": role, "content": content})
    result.append({"role": "user", "content": message.strip()})
    return result


def _completion(url: str, model: str, messages: list[dict], token: str = "", timeout: int = 20) -> str:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    body = json.dumps({"model": model, "messages": messages, "stream": False, "temperature": 0.2}).encode()
    req = Request(url + "/chat/completions", data=body, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read(2_000_000))
        answer = payload["choices"][0]["message"]["content"]
        if not isinstance(answer, str) or not answer.strip():
            raise InferenceUnavailable("Model returned an empty answer")
        return answer.strip()
    except (HTTPError, URLError, OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        raise InferenceUnavailable("Model provider unavailable or returned an invalid response") from exc


def infer(message: str, *, history: list | None = None, env: dict | None = None) -> InferenceResult:
    """Local-first. Cloud fallback only if explicitly enabled and configured."""
    env = os.environ if env is None else env
    messages = _messages(message, history)
    local_model = env.get("FINESSA_LOCAL_MODEL", "llama3.2")
    try:
        local_url = _endpoint(env, "FINESSA_LOCAL", "http://127.0.0.1:11434/v1")
        answer = _completion(local_url, local_model, messages)
        return InferenceResult(answer, "local", local_model)
    except InferenceUnavailable:
        pass
    if env.get("FINESSA_CLOUD_ENABLED", "").lower() not in ("1", "true", "yes"):
        raise InferenceUnavailable("Local model unavailable; cloud fallback is disabled")
    token = env.get("FINESSA_CLOUD_API_KEY", "")
    model = env.get("FINESSA_CLOUD_MODEL", "")
    if not token or not model:
        raise InferenceUnavailable("Cloud fallback requires a configured model and API key")
    url = _endpoint(env, "FINESSA_CLOUD", "https://api.openai.com/v1")
    return InferenceResult(_completion(url, model, messages, token), "cloud", model)
