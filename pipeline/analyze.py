"""
Two-step visual grounding:
1. MiniMax M3 writes a dense structured description from sampled frames.
2. MiniMax M3 checks that description against the same frames and removes
   anything unsupported or too generic.

The final verified description is what the caption model uses.
"""
import base64
import json
import re

from openai import OpenAI
from pydantic import ValidationError

from config import Config
from schemas import VideoBrief


def encode_image_base64(image_path: str) -> str:
    """Convert a local image file into a base64 data URI."""
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def _strip_to_json(text: str) -> dict:
    """Extract a JSON object from model output, tolerating markdown fences."""
    if not text:
        raise ValueError("Empty response from model.")

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        return json.loads(match.group(0))

    raise ValueError(f"Could not extract JSON from response: {text[:200]}")


def _build_brief_prompt(transcript: str) -> str:
    transcript_section = ""
    if transcript:
        transcript_section = f"""
The clip's audio was transcribed as follows (may include dialogue, narration, or ambient sounds):
"{transcript}"
"""

    return f"""You are analyzing a short video clip using the provided keyframes in chronological order.{transcript_section}

Produce a structured JSON brief that captures ONLY what is actually visible in the frames. Use exactly these fields:
- setting: where and when the video takes place
- subjects: the main people, animals, or entities visible
- actions: what the subjects are doing
- objects: notable objects, props, or environmental details
- mood: atmosphere or emotional tone
- sounds: notable non-speech sounds (or "none" if none)
- dialogue_summary: summary of spoken dialogue or narration, if any
- notable_details: any other distinctive visual details
- overall_summary: a concise 2-3 sentence summary
- facts: list of 5-10 short, independently-checkable claims about what is literally visible, ordered from most prominent/persistent to least

Rules:
- Describe ONLY what you can see in the provided frames.
- Do NOT invent animals, vehicles, objects, landmarks, locations, or people that are not clearly visible.
- If something is unclear or partially visible, describe it generically or omit it.
- Facts should be concrete enough that someone looking at the frames could verify them.
- Do not include explanations, markdown, or reasoning outside the JSON.

Output ONLY valid JSON matching this structure exactly:

{{
  "setting": "...",
  "subjects": "...",
  "actions": "...",
  "objects": "...",
  "mood": "...",
  "sounds": "...",
  "dialogue_summary": "...",
  "notable_details": "...",
  "overall_summary": "...",
  "facts": ["...", "..."]
}}
"""


def _brief_to_paragraph(brief: VideoBrief) -> str:
    """Flatten a structured brief into a concise, structured fact sheet."""
    return brief.to_text()


def _build_verify_prompt(draft: str) -> str:
    return f"""Here is a draft description of the video frames:

{draft}

Critique each specific concrete claim (objects, animals, vehicles, locations, text, landmarks). Decide if it is: (a) clearly visible, (b) a graphical overlay/watermark/transition, (c) partially visible or unclear, or (d) not supported.

Rewrite the description keeping only claims in category (a). Generalize category (b) only if central. Remove or generalize categories (c) and (d). Also remove or generalize exact quoted text, brand names, signs, ethnicity, identity labels, religion markers, and specific location claims (cities, countries, landmarks).

Keep the same structured format with these exact labels, one per line:
Summary: ...
Setting: ...
Subjects: ...
Actions: ...
Objects: ...
Mood: ...
Audio: ... (only if clearly present)
Details: ... (only if clearly present)
Verified facts:
- ...
- ...

Be concise. Remove unsupported facts. Do not add details not in the draft. Output only the rewritten description. Do not mention frames, AI, uncertainty, or analysis."""


def _call_vision_model(client: OpenAI, frame_paths: list[str], prompt: str, max_tokens: int) -> str:
    """Send frames + a text prompt to the vision model and return the text answer."""
    content: list[dict] = [{"type": "text", "text": prompt}]
    for path in frame_paths:
        content.append({
            "type": "image_url",
            "image_url": {"url": encode_image_base64(path)},
        })

    response = client.chat.completions.create(
        model=Config.FIREWORKS_VISION_MODEL,
        messages=[{"role": "user", "content": content}],
        max_tokens=max_tokens,
        temperature=0.1,
    )
    raw_text = response.choices[0].message.content
    if raw_text is None:
        # Surface what we can for debugging; some providers return empty content on refusal.
        print(f"  WARNING: vision model returned no content. Finish reason: {response.choices[0].finish_reason}")
        raise ValueError("Model returned no content.")
    return raw_text


def _generate_structured_brief(client: OpenAI, frame_paths: list[str], transcript: str) -> VideoBrief:
    """First call: produce a structured brief from frames + transcript."""
    last_error = None
    for attempt in range(2):
        try:
            raw_text = _call_vision_model(
                client, frame_paths, _build_brief_prompt(transcript), Config.BRIEF_MAX_TOKENS
            )
            parsed = _strip_to_json(raw_text)
            return VideoBrief(**parsed)
        except (ValidationError, ValueError, json.JSONDecodeError) as e:
            last_error = e
            print(f"  Brief attempt {attempt + 1} failed: {e}")

    raise RuntimeError(f"Could not produce valid video brief: {last_error}")


def _verify_description(client: OpenAI, frame_paths: list[str], draft_paragraph: str) -> str:
    """Second call: verify the brief against the frames and return a corrected plain-text description."""
    verified = _call_vision_model(
        client, frame_paths, _build_verify_prompt(draft_paragraph), Config.BRIEF_MAX_TOKENS
    )
    return verified.strip()


def analyze_video(frame_paths: list[str], transcript: str = "") -> str:
    """
    Generate a dense, verified plain-text description of the video.

    Returns a single paragraph the caption model can use as factual grounding.
    """
    client = OpenAI(
        api_key=Config.FIREWORKS_API_KEY,
        base_url=Config.FIREWORKS_BASE_URL,
    )

    brief = _generate_structured_brief(client, frame_paths, transcript)
    draft = _brief_to_paragraph(brief)
    verified = _verify_description(client, frame_paths, draft)
    return verified
