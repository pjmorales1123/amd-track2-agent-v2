# AMD Developer Hackathon — Track 2 Video Captioning Agent v2

A Dockerised agent that watches short video clips and generates captions in four styles: **formal**, **sarcastic**, **humorous_tech**, and **humorous_non_tech**.

This version uses a lean, two-step visual-grounding pipeline to produce accurate, style-specific captions.

## What makes it strong

- **Only 3–6 frames per clip** (dynamic by duration). Fewer tokens, faster calls, less rate-limit risk, while a strong vision model still sees enough.
- **Two-step visual grounding**: MiniMax M3 first writes a dense structured description, then MiniMax M3 verifies/corrects that description against the same frames. This removes hallucinated details before captions are written.
- **Kimi K2P6 for captions** with `reasoning_effort=none` so it returns clean caption text instead of reasoning traces.
- **Sequential style generation**: each style sees the previous captions and must use a different angle, so the four outputs do not sound like clones.
- **Keyword style guardrails**: tech captions must contain a tech word, sarcastic captions must contain a sarcasm marker; if not, the caption is regenerated once.
- **Optional local Whisper**: audio transcription is disabled by default, but can be enabled with `AUTO_TRANSCRIBE=true`.
- **Robustness**: retries on download, JSON repair, per-clip timeout, placeholder captions on failure.

## Pipeline

```
tasks.json
  -> download clip
  -> dynamic keyframe extraction (3–6 frames)
  -> optional local Whisper transcription
  -> MiniMax M3 structured brief
  -> MiniMax M3 verification/correction of the brief
  -> Kimi K2P6 style captions (sequential + guardrails)
  -> results.json
```

## Models

- **Vision / brief / verification:** Fireworks — `accounts/fireworks/models/minimax-m3`
- **Captions:** Fireworks — `accounts/fireworks/models/kimi-k2p6` with `reasoning_effort=none`
- **Transcription (optional):** local `faster-whisper` `tiny`

## Environment variables

```bash
# Required
FIREWORKS_API_KEY=your_key_here

# Optional (defaults shown)
FIREWORKS_BASE_URL=https://api.fireworks.ai/inference/v1
FIREWORKS_VISION_MODEL=accounts/fireworks/models/minimax-m3
FIREWORKS_TEXT_MODEL=accounts/fireworks/models/kimi-k2p6
REASONING_EFFORT=none

AUTO_TRANSCRIBE=false
WHISPER_MODEL=tiny
WHISPER_FALLBACK_MODEL=tiny
WHISPER_CACHE_DIR=/app/models
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8

SCENE_THRESHOLD=0.3
FRAMES_SHORT=3
FRAMES_MEDIUM=5
FRAMES_LONG=6
ABSOLUTE_MAX_FRAMES=6
KEYFRAME_JPEG_QUALITY=4
KEYFRAME_MAX_LONG_SIDE=1024

CAPTION_MAX_TOKENS=200
BRIEF_MAX_TOKENS=1500
PER_CLIP_TIMEOUT_SECONDS=120
MAX_CONCURRENT_CLIPS=3

INPUT_PATH=/input/tasks.json
OUTPUT_PATH=/output/results.json
```

## Build and push

### Option A — GitHub Actions (recommended if Docker Desktop fails)

1. Push this repo to GitHub.
2. In the repo settings, add this secret:
   - `DOCKERHUB_TOKEN` — your Docker Hub access token (not your password)
3. Go to **Actions → Build and push Track 2 image → Run workflow**.
4. The workflow builds for `linux/amd64` and pushes to `pjmorales04/amd-track2-agent-v2:latest`.

### Option B — Docker Desktop locally

```bash
docker buildx build --platform linux/amd64 -t your-registry/amd-track2-agent-v2:latest --push .
```

### Run the container

```bash
docker run --rm \
  -e FIREWORKS_API_KEY=... \
  -v "$(pwd)/examples:/input:ro" \
  -v "$(pwd)/output:/output" \
  your-registry/amd-track2-agent-v2:latest
```

### Local test (requires FFmpeg)

```bash
pip install -r requirements.txt
export FIREWORKS_API_KEY=...
python agent.py
```

## I/O format

**Input** (`/input/tasks.json`):

```json
[
  {
    "task_id": "v1",
    "video_url": "https://storage.googleapis.com/amd-hackathon-clips/1860079-uhd_2560_1440_25fps.mp4",
    "styles": ["formal", "sarcastic", "humorous_tech", "humorous_non_tech"]
  }
]
```

**Output** (`/output/results.json`):

```json
[
  {
    "task_id": "v1",
    "captions": {
      "formal": "...",
      "sarcastic": "...",
      "humorous_tech": "...",
      "humorous_non_tech": "..."
    }
  }
]
```

## Project structure

```
.
├── agent.py                 # Main orchestration
├── config.py                # Environment-based configuration
├── schemas.py               # Pydantic output schemas
├── requirements.txt
├── Dockerfile
├── README.md
├── examples/tasks.json      # Official example tasks
└── pipeline/
    ├── extract.py           # Download + dynamic keyframes + audio
    ├── transcribe.py        # Local faster-whisper transcription
    ├── analyze.py           # MiniMax M3 brief + verification
    └── caption.py           # Kimi K2P6 sequential style captions
```

## Rules compliance

- Reads `/input/tasks.json` and writes `/output/results.json`.
- Container base is `python:3.11-slim` with a `linux/amd64` manifest.
- Image size is well under 10 GB.
- Exits `0` on success and `1` only for fatal configuration errors.
- Finishes within the 10-minute limit via concurrency and per-clip timeouts.
- No hardcoded API keys or model restrictions.
