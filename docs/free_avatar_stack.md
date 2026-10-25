# Finessa free local avatar stack

This project now includes a no-cloud local avatar pipeline scaffold that follows the architecture below:

- InsightFace for camera/face verification
- Ollama for local chat
- Piper or espeak for local TTS
- SadTalker for avatar animation
- WebRTC/browser frontend for real-time voice/video interaction

## Environment variables

Add the following to `.env` or your runtime environment:

```bash
FINESSA_AVATAR_MODE=local_free
FINESSA_OLLAMA_MODEL=llama3.1
FINESSA_PIPER_MODEL=
FINESSA_SADTALKER_HOME=/path/to/SadTalker
FINESSA_AVATAR_REF_IMAGE=/path/to/reference_face.png
FINESSA_AVATAR_MATCH_THRESHOLD=0.5
```

`FINESSA_AVATAR_REF_IMAGE` is optional for testing. If it is absent, the system will allow a detected face but will log a warning instead of enforcing a match.

## Core flow

1. Browser captures a still frame from the user camera.
2. Backend runs InsightFace to detect a face.
3. If a reference image is configured, it compares embeddings and only proceeds when the distance is below the threshold.
4. User prompt is sent to Ollama.
5. Local TTS converts the reply to WAV audio.
6. SadTalker optionally animates the selected portrait with the generated speech.

## Local commands

```bash
# install Ollama
# https://ollama.com/download

ollama pull llama3.1

# install Piper or espeak for local TTS
# then export FINESSA_PIPER_MODEL or ensure piper is on PATH

# clone SadTalker locally
git clone https://github.com/OpenTalker/SadTalker.git
export FINESSA_SADTALKER_HOME=$PWD/SadTalker
```

## API endpoints

- `GET /avatar` renders the local avatar dashboard
- `GET /api/avatar/status` reports which local services are available
- `POST /api/avatar/verify` accepts a base64-encoded image and returns a verification decision
- `POST /api/avatar/chat` accepts a prompt and returns the local model response

## Notes

This is a scaffold for a free architecture. Real-time motion and voice transport still depends on a browser/WebRTC client and local model availability.
