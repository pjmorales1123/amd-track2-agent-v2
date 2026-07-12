"""
Pydantic schemas for every structured output in the pipeline.
"""
from pydantic import BaseModel, Field


class VideoBrief(BaseModel):
    """Structured scene understanding produced by the vision model."""

    setting: str = Field(description="Where and when the video takes place.")
    subjects: str = Field(description="People, animals, or main entities visible.")
    actions: str = Field(description="What the subjects are doing.")
    objects: str = Field(description="Notable objects, props, or environmental details.")
    mood: str = Field(description="Atmosphere or emotional tone of the clip.")
    sounds: str = Field(description="Notable non-speech sounds if any, otherwise 'none'.")
    dialogue_summary: str = Field(
        description="Summary of spoken dialogue or narration, if any."
    )
    notable_details: str = Field(
        description="Any other distinctive details worth mentioning."
    )
    overall_summary: str = Field(
        description="2-3 sentence summary of the video's content."
    )
    facts: list[str] = Field(
        default_factory=list,
        description="5-10 short, independently-checkable claims visible in the frames, "
                    "ordered from most prominent/persistent to least.",
    )

    def to_text(self) -> str:
        """Flatten the brief into a readable block for text-only caption models."""
        lines = [
            f"Summary: {self.overall_summary}",
            f"Setting: {self.setting}",
            f"Subjects: {self.subjects}",
            f"Actions: {self.actions}",
            f"Objects: {self.objects}",
            f"Mood: {self.mood}",
        ]
        if self.dialogue_summary and self.dialogue_summary.lower() not in {"none", "n/a", ""}:
            lines.append(f"Audio: {self.dialogue_summary}")
        if self.notable_details and self.notable_details.lower() not in {"none", "n/a", ""}:
            lines.append(f"Details: {self.notable_details}")
        if self.facts:
            lines.append("Verified facts:")
            lines.extend(f"- {f}" for f in self.facts)
        return "\n".join(lines)


class StyledCaptions(BaseModel):
    """Final captions in each required style."""

    formal: str = Field(description="Professional, objective, factual tone.")
    sarcastic: str = Field(description="Dry, ironic, lightly mocking tone.")
    humorous_tech: str = Field(
        description="Funny caption with technology or programming references."
    )
    humorous_non_tech: str = Field(
        description="Funny, everyday humour with no technical jargon."
    )


class CandidateScore(BaseModel):
    """Judge score for a single caption candidate."""

    accuracy: float = Field(
        ge=0.0, le=1.0, description="How faithfully the caption reflects the video."
    )
    style_match: float = Field(
        ge=0.0, le=1.0, description="How well the caption matches the requested tone."
    )
    feedback: str = Field(
        description="Brief, specific reason for the scores and how to improve."
    )


class StyleCandidateScores(BaseModel):
    """Judge output for the candidate set of one style."""

    candidate_0: CandidateScore
    candidate_1: CandidateScore


class CaptionResult(BaseModel):
    """One entry in results.json."""

    task_id: str
    captions: StyledCaptions
