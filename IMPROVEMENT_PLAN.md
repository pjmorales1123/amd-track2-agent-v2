# Improvement Suggestions — Validation & Plan

## Current status

- Score: **0.92** (tied for top 3)
- The current pipeline is already excellent. At this level, changes are high-risk / low-reward.
- Any modification should be A/B tested against the current pipeline before shipping.

## Suggestion-by-suggestion assessment

### 1. Replace first/last-frame sampling with stable temporal coverage

**Verdict: IMPLEMENT**
- **Chance of improvement:** High
- **Risk:** Low
- **Why:** First and last frames frequently contain fades, title cards, black frames, or motion blur. Mid-segment frames are more representative of actual content.
- **Implementation:** Change `build_keyframe_timestamps` to prefer midpoints of equal temporal segments, then add scene-change frames only if they differ meaningfully from those midpoints.
- **Recommended frame count:** 4 for short clips, 6 for normal, 8 only for long/dynamic clips.

### 2. Give Kimi structured confirmed facts instead of one flattened paragraph

**Verdict: TEST CAREFULLY**
- **Chance of improvement:** Moderate
- **Risk:** Medium
- **Why:** Structured facts could improve accuracy, but Kimi may not handle raw JSON as naturally as prose. The current flattened paragraph works well.
- **Implementation (if tested):** Keep the verified brief but send it as a clean bullet list rather than a dense paragraph. This preserves readability while separating facts.
- **Do not:** Send raw nested JSON to the caption model unless few-shot examples prove it follows the structure.

### 3. Add carefully chosen few-shot examples for style

**Verdict: IMPLEMENT**
- **Chance of improvement:** High, especially for humorous styles
- **Risk:** Low
- **Why:** Current style prompts are definitions only. A judge evaluates register, not keyword presence. Good few-shot examples show the model what each style actually sounds like.
- **Implementation:** Add 2 short examples per style in the system prompt. Include one bad example per style showing what to avoid. Keep examples unrelated to common video topics.

### 4. Shorten target caption length

**Verdict: IMPLEMENT WITH STYLE-SPECIFIC RANGES**
- **Chance of improvement:** Moderate-High
- **Risk:** Low if done carefully
- **Why:** 25–60 words is generous. Extra clauses increase hallucination and filler risk. Shorter, specific captions score better.
- **Implementation:**
  - Formal: 15–28 words
  - Sarcastic: 12–24 words
  - Humorous tech: 15–28 words
  - Humorous non-tech: 12–24 words
- **Guard against:** Vague-but-true captions. Require central subject + action.

### 5. Add a claim-based final validator

**Verdict: OPTIONAL / LOW PRIORITY**
- **Chance of improvement:** Moderate
- **Risk:** Medium-High
- **Why:** Could catch hallucinations, but may falsely flag figurative language in humorous captions ("the dog's GPS crashed" is fine if dog moves wrong way, even though GPS isn't real).
- **Implementation (if done):** Simple noun/verb extraction + approved-metaphor whitelist. Only block clearly unsupported concrete claims (breeds, brands, locations, exact professions).
- **Recommendation:** Skip unless harness testing shows clear accuracy gains.

### 6. Build a small local scoring harness

**Verdict: DO THIS FIRST**
- **Chance of finding improvements:** Very high
- **Risk:** None (development only)
- **Why:** At 0.92, untested changes can easily lower the score. Need objective A/B comparison.
- **Implementation:**
  - 8–12 representative public clips
  - Run current pipeline and candidate pipeline
  - Use a strong multimodal judge (MiniMax M3 or Kimi with images) to score accuracy and style separately
  - Randomize A/B order to avoid bias
  - Only ship changes that win across multiple clips

## Recommended execution order

1. Build the evaluation harness (#6).
2. Implement temporal midpoint sampling (#1) and test.
3. Implement few-shot style examples (#3) and test.
4. Implement shorter length targets (#4) and test.
5. Only then consider structured facts (#2) or claim validator (#5).

## Important caution

Do not ship all six changes at once. The current 0.92 score means the pipeline is already near the accuracy/style ceiling. Iterative A/B testing is the only safe way to improve further.
