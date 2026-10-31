"""
Signal two: the style signal. ← YOU BUILD THIS IN MILESTONE 4

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

Three measures are stubbed below because the brief names those three. They are
stubs, not implementations: what they compute is yours, and so is how you
combine them.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how varied?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import re
import statistics


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures — YOU BUILD THESE ─────────────────────────────────────

def sentence_length_spread(text: str) -> float:
    """
    How much sentence length varies. ← TODO

    Returns:
        A float. Decide yourself what scale it's on and which direction means
        "more human" — then write that down, because your combining rule
        depends on knowing it.

    A hint on what you're reaching for: the standard deviation of sentence
    lengths, probably divided by the mean so a long text and a short one are
    comparable. `statistics.stdev` is imported for you.

    Watch the edge case: a one-sentence submission has no spread at all, and
    `stdev` raises on fewer than two values. Decide what that should return
    before the attack set decides for you.

    Mine: coefficient of variation (stdev / mean) of words per sentence. Higher
    means lumpier, which reads more human. Fewer than 2 sentences returns 0.0,
    but `style_signal` treats texts under MIN_SENTENCES as "no evidence" rather
    than as perfectly even.
    """
    lengths = [len(words(s)) for s in sentences(text)]
    lengths = [n for n in lengths if n > 0]
    if len(lengths) < 2:
        return 0.0
    mean = statistics.mean(lengths)
    return round(statistics.stdev(lengths) / mean, 4)


def type_token_ratio(text: str) -> float:
    """
    Unique words over total words. ← TODO

    Returns:
        A float between 0 and 1. Higher means more varied vocabulary.

    Worth knowing before you rely on it: this measure falls as text gets
    longer, because common words repeat. Two texts of different lengths aren't
    directly comparable on it, and if your test inputs vary a lot in length,
    that alone can look like a signal.

    Mine is the moving-average version (MATTR): the plain ratio inside every
    TTR_WINDOW-word window, averaged. Every window is the same size, so a long
    text and a short one are comparable. Under one window of words, it falls
    back to the plain ratio.
    """
    w = words(text)
    if not w:
        return 0.0
    if len(w) <= TTR_WINDOW:
        return round(len(set(w)) / len(w), 4)
    ratios = [
        len(set(w[i:i + TTR_WINDOW])) / TTR_WINDOW
        for i in range(len(w) - TTR_WINDOW + 1)
    ]
    return round(statistics.mean(ratios), 4)


def punctuation_density(text: str) -> float:
    """
    How much punctuation, relative to length. ← TODO

    Returns:
        A float. Whether you count all punctuation or only some kinds — commas,
        semicolons, dashes — is a real choice. Semicolons and em dashes are
        more interesting than full stops, because they vary more between
        writers.

    Mine counts only the marks that vary between writers — ; : ( ) ? ! and
    dashes (em, en, or a spaced hyphen) — per 100 words. Full stops and commas
    are left out: every writer uses them. Higher reads more human.
    """
    w = words(text)
    if not w:
        return 0.0
    marks = len(re.findall(r"[;:()?!\u2014\u2013]|\s-{1,2}\s", text))
    return round(100 * marks / len(w), 4)


# ── Combining them ───────────────────────────────────────────────────────────

# Below this many sentences, spread is noise and counts as "no evidence".
MIN_SENTENCES = 3
TTR_WINDOW = 50

# Each measure maps onto 0–1 AI-likeness with a straight line between two
# anchors: at `ai` it scores 1.0, at `human` 0.0, clamped either side.
# Calibrated on the inputs in calibrate.py — rerun it if you move these.
SPREAD_ANCHORS = {"ai": 0.20, "human": 0.65}       # coefficient of variation
# ⚠️ Flipped from the textbook direction: in calibration the AI text had the
# MOST varied vocabulary and the human texts repeated words. Models are tuned to
# avoid repetition; people repeat themselves. Higher variety = more AI here.
TTR_ANCHORS = {"ai": 0.90, "human": 0.72}          # MATTR, 50-word windows
PUNCT_ANCHORS = {"ai": 0.0, "human": 4.0}          # marks per 100 words

# How much each measure counts. Spread is the most reliable of the three;
# punctuation the least (modern models love a colon or a dash).
MEASURE_WEIGHTS = {"spread": 0.45, "ttr": 0.35, "punct": 0.20}


def _ai_likeness(value: float, anchors: dict) -> float:
    """Place a raw measure on 0 (human end) … 1 (AI end), clamped. Works
    whichever way round the anchors are."""
    span = anchors["human"] - anchors["ai"]
    return min(max((anchors["human"] - value) / span, 0.0), 1.0)


def measure_scores(text: str) -> dict:
    """Each measure as 0–1 AI-likeness, before weighting. For debugging."""
    spread = (
        _ai_likeness(sentence_length_spread(text), SPREAD_ANCHORS)
        if len(sentences(text)) >= MIN_SENTENCES else 0.5
    )
    return {
        "spread": round(spread, 4),
        "ttr": round(_ai_likeness(type_token_ratio(text), TTR_ANCHORS), 4),
        "punct": round(_ai_likeness(punctuation_density(text), PUNCT_ANCHORS), 4),
    }

def style_signal(text: str) -> float:
    """
    The style signal as a 0–1 score. **Higher means more likely AI.** ← TODO

    Combine your three measures into one number. Same direction as
    `detector.model_signal`, so that `scoring.combine_signals` can treat them
    the same way — if one of your signals runs backwards, everything above it
    is wrong in a way that's hard to see.

    Two things to decide and write down:

      1. Which direction each measure points. Low spread means more AI-ish, so
         it needs flipping. Work out which of your three need that.
      2. How to get each onto a comparable scale. A raw type-token ratio sits
         between 0 and 1; a raw punctuation count doesn't. Adding them
         unscaled means whichever has the bigger numbers wins by default.

    Test it on the four calibration inputs from Milestone 4 — clearly AI,
    clearly human, plain conventional human writing, lightly-edited AI — before
    you trust it. Plain and ordinary, not formal: formal prose reads as *human*
    to signal one, and it is plain writing that gets accused.

    Mine: spread and punctuation point "higher = more human" raw; type-token
    ratio points "higher = more AI" (see TTR_ANCHORS). `_ai_likeness` puts
    each onto 0–1 AI-likeness between its calibrated anchors, whichever way
    they run, and MEASURE_WEIGHTS combines them.
    """
    scores = measure_scores(text)
    total = sum(MEASURE_WEIGHTS[k] * scores[k] for k in MEASURE_WEIGHTS)
    return round(total, 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text)}")
    print(f"type_token_ratio         {type_token_ratio(text)}")
    print(f"punctuation_density      {punctuation_density(text)}")
    print(f"measure_scores           {measure_scores(text)}   (0 human … 1 AI)")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
