"""
Style-specific caption generation.

- Uses Kimi K2P6 with reasoning_effort=none for clean, non-reasoning output.
- Default mode: sequential per-style captions.
- Experimental formal_grounded mode: write a verified formal caption first, then
  lock the humorous/sarcastic styles to the same entities to reduce hallucination.
- Verifies captions against keyword heuristics and retries once if the style is weak.
"""
from openai import OpenAI

from config import Config


# Keywords that signal the requested style is actually present.
TECH_STYLE_WORDS = {
    "api", "bug", "cache", "commit", "debug", "deploy", "latency", "log",
    "pipeline", "queue", "rollback", "runtime", "scheduler", "server",
    "thread", "packet", "loop", "function", "variable", "compile",
    "render", "frame rate", "fps", "bandwidth", "cpu", "gpu",
    "memory", "overflow", "underflow", "exception", "crash", "reboot",
}

SARCASM_MARKERS = {
    "apparently", "because", "clearly", "naturally", "of course", "obviously",
    "serious", "thrilling", "groundbreaking", "fascinating", "riveting",
    "nothing says", "nothing screams", "truly", "sure",
}


STYLE_PROMPTS = {
    "formal": (
        "Write a formal, professional, objective caption. Factual tone, no humor, "
        "no slang, no embellishment. State the central subject and action clearly.\n\n"
        "Example:\n"
        "A dog runs across a grassy field to retrieve a thrown ball.\n\n"
        "Bad example (too vague):\n"
        "Something happens outside."
    ),
    "sarcastic": (
        "Write a sarcastic caption: dry, ironic, lightly mocking, grounded in the "
        "specific action described. Stay lighthearted and non-offensive. Mock the "
        "action, not the subject.\n\n"
        "Example:\n"
        "Another flawless demonstration of how repeatedly pawing a closed door "
        "definitely makes it open faster.\n\n"
        "Bad example (too generic):\n"
        "Clearly, this door is going to open any second now."
    ),
    "humorous_tech": (
        "Write a funny caption using technology, software, programming, network, "
        "game engine, or debugging references. The tech reference should be natural "
        "and the caption should still describe the video.\n\n"
        "Example:\n"
        "The cat’s edge-detection algorithm successfully identified the cup as a "
        "pushable object and executed the knockover routine.\n\n"
        "Bad example (forced):\n"
        "This cat is like a computer that crashed."
    ),
    "humorous_non_tech": (
        "Write a funny everyday-humor caption with no technical jargon. Relatable, "
        "light-hearted, and grounded in the video.\n\n"
        "Example:\n"
        "When you confidently leave the house without an umbrella and the sky "
        "immediately files a complaint.\n\n"
        "Bad example (too generic):\n"
        "This person is having a bad day."
    ),
}


def _clean_caption(text: str) -> str:
    """Strip surrounding quotes and whitespace from a caption."""
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        text = text[1:-1].strip()
    return text


def _needs_style_retry(style: str, caption: str) -> bool:
    """Check if a caption obviously misses its style target."""
    normalized = caption.lower()
    if style == "humorous_tech":
        return not any(word in normalized for word in TECH_STYLE_WORDS)
    if style == "sarcastic":
        return not any(marker in normalized for marker in SARCASM_MARKERS)
    return False


def _generate_caption(
    client: OpenAI,
    description: str,
    style: str,
    prior_captions: list[str],
    grounding_note: str = "",
) -> str:
    """Generate one caption for a style."""
    variety_note = ""
    if prior_captions:
        variety_note = (
            "\n\nCaptions already written for this clip in other styles. "
            "Use a different sentence structure and comedic angle: "
            + " | ".join(prior_captions)
        )

    prompt = (
        f"{STYLE_PROMPTS[style]}\n\n"
        "Critical rules:\n"
        "- Mention the central subject and action. Omit secondary details unless essential.\n"
        "- Stay factually grounded in the description below. Do not invent details.\n"
        "- Do not name cities, countries, landmarks, or specific locations.\n"
        "- Do not mention ethnicity, identity labels, religion markers, brand names, or signs unless explicitly present.\n"
        "- Never mention computer vision, models, detection, frames, prompts, pipelines, or uncertainty.\n"
    )
    if grounding_note:
        prompt += grounding_note + "\n"
    prompt += (
        f"\nFactual description of the video:\n{description}\n\n"
        "Write ONE caption, one or two sentences, roughly 15 to 35 words. "
        "Write as if you personally watched the video. Output only the caption text."
        f"{variety_note}"
    )

    response = client.chat.completions.create(
        model=Config.FIREWORKS_TEXT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=Config.CAPTION_MAX_TOKENS,
        temperature=0.75 if style in {"sarcastic", "humorous_tech", "humorous_non_tech"} else 0.3,
        extra_body={"reasoning_effort": Config.REASONING_EFFORT},
    )
    text = response.choices[0].message.content
    if text is None:
        raise ValueError("Model returned no content.")
    return _clean_caption(text)


def _generate_with_retry(
    client: OpenAI,
    description: str,
    style: str,
    prior: list[str],
    grounding_note: str = "",
) -> str:
    """Generate a caption, retrying once if style heuristics fail."""
    caption = _generate_caption(client, description, style, prior, grounding_note)
    if _needs_style_retry(style, caption):
        print(f"  {style}: retrying weak caption...")
        caption = _generate_caption(client, description, style, prior, grounding_note)
    return caption


def _generate_sequential(client: OpenAI, description: str) -> dict[str, str]:
    """Original sequential generation: each style sees prior captions for variety."""
    results: dict[str, str] = {}
    prior: list[str] = []

    for style in Config.REQUIRED_STYLES:
        try:
            caption = _generate_with_retry(client, description, style, prior)
            results[style] = caption
            prior.append(caption)
        except Exception as e:
            print(f"  Caption generation failed for {style}: {e}")
            results[style] = f"Unable to generate a {style} caption for this clip."
            prior.append(results[style])

    return results


def _generate_formal_grounded(client: OpenAI, description: str) -> dict[str, str]:
    """
    Write the formal caption first, then constrain other styles to reuse only
    subjects/actions/objects named in that formal caption. This reduces the chance
    that humorous or sarcastic captions drift into unsupported details.
    """
    results: dict[str, str] = {}

    # 1. Formal first.
    try:
        results["formal"] = _generate_with_retry(client, description, "formal", [])
    except Exception as e:
        print(f"  Formal caption generation failed: {e}")
        # Fall back to sequential if formal fails.
        return _generate_sequential(client, description)

    formal_text = results["formal"]
    grounding = (
        f"\nLOCKED GROUNDING CAPTION (formal, already verified):\n"
        f'"{formal_text}"\n'
        "Every other caption MUST reuse only the subjects, actions, and objects "
        "named in that formal caption. Do not introduce new background colours, "
        "counts, side details, or entities not mentioned in the formal caption."
    )

    # 2. Other styles, locked to the formal caption.
    other_styles = [s for s in Config.REQUIRED_STYLES if s != "formal"]
    prior: list[str] = []
    for style in other_styles:
        try:
            caption = _generate_with_retry(client, description, style, prior, grounding)
            results[style] = caption
            prior.append(caption)
        except Exception as e:
            print(f"  Caption generation failed for {style}: {e}")
            results[style] = f"Unable to generate a {style} caption for this clip."
            prior.append(results[style])

    return results


def generate_captions(description: str) -> dict[str, str]:
    """
    Generate captions for all four styles.

    Mode is chosen by Config.CAPTION_MODE:
      - "sequential" (default): each style is generated in order with prior captions visible.
      - "formal_grounded": formal is generated first, then other styles are locked to it.
    """
    client = OpenAI(
        api_key=Config.FIREWORKS_API_KEY,
        base_url=Config.FIREWORKS_BASE_URL,
    )

    mode = getattr(Config, "CAPTION_MODE", "sequential").strip().lower()
    if mode == "formal_grounded":
        return _generate_formal_grounded(client, description)
    return _generate_sequential(client, description)
