# Hybrid AI development configuration

Finessa uses an optional local-first, OpenAI-compatible chat-completions adapter.
The existing rule-based assistant remains the fallback.

## Local development

Install and run a compatible local model server (e.g., Ollama with a downloaded model).
Set environment variables before starting Flask:

```sh
export FINESSA_AI_ENABLED=1
export FINESSA_LOCAL_URL=http://127.0.0.1:11434/v1
export FINESSA_LOCAL_MODEL=llama3.2
python app.py
```

The server must actually be running and have the selected model installed.
No model is bundled in this repository.

## Optional cloud fallback

Cloud is **disabled by default**. Enabling it transmits the user's chat message
to the configured external provider. Do not enable for confidential case
information without an explicit user-facing consent and data handling review.

```sh
export FINESSA_CLOUD_ENABLED=1
export FINESSA_CLOUD_URL=https://api.openai.com/v1
export FINESSA_CLOUD_MODEL=<your-provider-model-id>
export FINESSA_CLOUD_API_KEY=<secret>
```

Never commit keys. HTTPS is mandatory for cloud requests. The Flask chat
endpoint does not forward case workspace content or a case ID to the model,
but the **user's message itself may contain sensitive information**.
Production work must add per-user cloud consent and privacy controls.

## Tests

```sh
python -m unittest tests.test_hybrid_ai tests.test_hybrid_endpoint -v
python -m unittest discover -s tests -v
```

These tests mock model responses; they do not certify provider availability,
legal accuracy, citation correctness, or end-to-end public readiness.

## Current limitations

- Chat history is not yet persisted or sent by the Flask endpoint.
- The adapter is a text model only: voice, lip sync and avatar motion are separate work.
- Local model latency and quality depend on the device and model.
- A general model answer is not a verified legal authority. The local research
  results remain separate and require independent source validation.
- User-controlled provider selection, timeouts, quotas, rate limits, streaming,
  structured tool calling, and consent UX remain beta blockers.
