# Cross-Repo Analysis: All Public 0.92 Track 2 Submissions

## Purpose

We are tied for first place with a **0.92** score. Before risking that score with "improvements," I inspected every other public repository that also reports 0.92 to see whether they share a common recipe or hit the same ceiling.

## Repositories examined

| Repository | Reported score | Code status | Approach |
|------------|----------------|-------------|----------|
| `Anushiv7/DescribeX` | 0.92 | Full code | Extract frames → base64 → Kimi K2P6 scene description → GPT-OSS-120b style captions |
| `iiTzThoha/video-caption-agent` | 0.92 | Full code | MiniMax M3 native video URL → description → all styles in one JSON call |
| `nhegde610/track2-amd-hackathon` | 0.92 | **Placeholder only** | No code available |
| `yash-kumarx/amd-hackathon-video-captioning` | 0.92 | Full code + evaluator replica | Midpoint frame sampling, short captions, style exemplars |
| `pjmorales1123/amd-track2-agent-v2` (ours) | 0.92 | Full code | Scene-aware keyframes → MiniMax M3 brief → MiniMax M3 verify → Kimi K2P6 sequential captions |

## What each competitor actually does

### 1. DescribeX (`Anushiv7/DescribeX`)

- **Frame handling**: FFmpeg extracts up to 60 frames, then uniform sampling down to 16 frames. Always keeps first and last frame.
- **Vision prompt**: Asks for 7 categories (scene, subjects, actions, environment, mood, key visual elements, temporal flow). Dense prose, not JSON.
- **Caption prompt**: 2–4 sentences per style. Plain style definitions, no exemplars.
- **Models**: `kimi-k2p6` for vision, `gpt-oss-120b` for text.
- **Architecture**: Full Next.js web app + Python engine. Docker entrypoint wraps the engine.
- **Notable**: They sample **16 frames** and still score 0.92 — more frames does not obviously mean a better score.

### 2. Video Caption Agent (`iiTzThoha/video-caption-agent`)

- **Frame handling**: None. Sends the video URL directly to MiniMax M3 (`accounts/fireworks/models/minimax-m3`).
- **Vision prompt**: One call: "Describe this video factually and specifically, in 5–7 sentences."
- **Caption prompt**: One call generates all four styles as JSON. Style definitions only, no exemplars.
- **Total API calls**: **2 per video**.
- **Error handling**: Writes empty captions on failure, exits 0.
- **Notable**: The simplest possible pipeline still scores 0.92.

### 3. yash-kumarx (`yash-kumarx/amd-hackathon-video-captioning`)

- **Frame handling**: 6–8 midpoint frames (segment midpoints), 768 px long side.
- **Evaluator replica**: Includes a local judge that scores accuracy + style, averaged.
- **Caption length target**: 8–32 words.
- **Style prompts**: Rubrics + few-shot exemplars.
- **Facts**: Structured JSON evidence passed to caption model.
- **Notable**: This is the only repo that ships an evaluator, so its advice is evidence-based but still *replica*-based.

### 4. Ours (`pjmorales1123/amd-track2-agent-v2`)

- **Frame handling**: Scene-aware keyframes (3–6), always includes first/last, fills with evenly-spaced frames.
- **Vision prompt**: Structured JSON brief + separate verification pass.
- **Caption prompt**: Sequential per-style generation, keyword guardrails, 25–60 word target.
- **Models**: MiniMax M3 for vision/verification, Kimi K2P6 for captions.
- **Total API calls**: 2 vision + up to 8 caption (with retries).

## Common patterns across all working 0.92 submissions

1. **All use Fireworks AI** as the provider.
2. **All use multimodal vision** (frames or native video) plus a text/vision model for captions.
3. **All keep captions grounded** in a factual scene understanding step.
4. **None use audio/transcription** in the final scoring path (DescribeX may support it in the web app, but the Docker path is frame-only).
5. **All four styles are generated** from the same source understanding.
6. **All exit 0** even if individual tasks fail.

## Key differences that do NOT correlate with score

| Dimension | Range across 0.92 repos |
|-----------|------------------------|
| Frame count | 0 (native video) → 6 → 16 |
| Frame selection | Scene detection, midpoints, uniform, native video |
| Vision model | MiniMax M3, Kimi K2P6 |
| Caption model | Kimi K2P6, GPT-OSS-120b, MiniMax M3 |
| Caption length | 8–32 words → 2–4 sentences → 25–60 words |
| Style guidance | Definitions only → rubrics + exemplars |
| API calls | 2 → 10+ |

## What this tells us about the 0.92 score

The fact that four very different architectures all land on **exactly 0.92** strongly suggests one of two things:

1. **We are at or near the scoring ceiling** for the current judge/evaluator/model combination. Further architectural changes give diminishing returns.
2. **The hidden test set and judge have a ceiling** where perfect accuracy and style alignment is hard to achieve consistently, regardless of approach.

Either interpretation means the same thing for strategy: **marginal changes have small upside and meaningful downside risk.**

## How much should we trust the yash-kumarx evaluator replica?

**Verdict: plausible but unconfirmed.**

Reasons to take it seriously:
- It was built from the participant guide language.
- Its two-axis scoring (accuracy + style, averaged) matches what every top team optimizes for.
- The recommended interventions (midpoint frames, shorter captions, exemplars) are low-risk.

Reasons to stay skeptical:
- No official Lablab evaluator source code is public.
- The real judge may use a different model, different weights, or different few-shot examples.
- A replica can overfit to its own judge; changes that help the replica may not help the real evaluator.

## Strategic recommendation

Given the evidence:

1. **Do not change the submitted Docker image** (`pjmorales04/amd-track2-agent-v2:latest`) unless we have strong local A/B evidence that a change improves captions.
2. **The safest use of remaining time** is submission packaging: 16:9 cover image, slides PDF, demo video, and description fields.
3. **If we want to experiment**, do it on a separate Docker tag (e.g., `:experimental`) and run a local evaluator on held-out clips. Do not overwrite `:latest` until the experimental version clearly wins.
4. **The low-risk improvements** (midpoint frame sampling, shorter captions, style exemplars) are worth testing, but each has only a small chance of raising a 0.92 score. They have a non-zero chance of lowering it.

## What would change my recommendation

If any of the following happen, experimentation becomes more attractive:
- A local evaluator shows a clear win (>0.02 improvement) across multiple representative clips.
- We discover that the real judge uses the exact yash-kumarx replica (unlikely but possible).
- The competition allows unlimited resubmissions with no penalty for lower scores.

Without one of those, **freeze the current submission and focus on presentation.**
