# Milestone 1 — Tracing a submission

Written before any of `/submit`, `/appeal`, `stylometry.py` or `scoring.py`
exists. This is the contract the rest of the build has to keep.

---

## 1. The path a piece of text takes

From arriving at the service to the label a reader sees:

1. **Flask receives `POST /submit`** (`app.py::submit`).
   Adds: the raw body parsed into a Python dict — or nothing, if the body
   isn't JSON or isn't an object.

2. **The route checks the input and gives it an identity** (`app.py::submit`).
   Adds: a guarantee that `text` is a non-empty string within the length
   limits and `creator_id` is present — or an early `4xx` error plus a
   `rejected` entry via `audit.log_rejection`. A text that passes gets a
   fresh `content_id` (`uuid4`), which is the handle every later step, the
   log and the appeal use.

3. **Signal one reads it for predictability** (`detector.model_signal`).
   Adds: `model_score`, 0–1, higher = more AI-like. gpt2 computes perplexity
   on **the first 400 tokens only** (~300 words) and a logistic curve squashes
   it (perplexity 45 → 0.5).

4. **Signal two measures its shape** (`stylometry.style_signal`).
   Adds: `style_score`, 0–1, higher = more AI-like, built from sentence-length
   spread, vocabulary variety and punctuation variety over **the whole text**.

5. **The combining rule makes one number** (`scoring.combine_signals`).
   Adds: `combined_score`, 0–1. This is where the false-positive policy lives
   (see section 3).

6. **The label mapping turns the number into words** (`scoring.score_to_label`).
   Adds: `guess` (`"human"` / `"unsure"` / `"ai"`), the full `label` sentence a
   person reads, and `confidence`.

7. **The decision is logged, then returned** (`audit.log_decision`, then the
   JSON response).
   Adds: a permanent, append-only record with all nine fields and
   `status: "decided"`; then the writer gets back the label, the
   `content_id` they'd need to appeal, and both signal scores.

The appeal is a short second path: `POST /appeal` → look up `content_id` with
`audit.entries_for` → `audit.log_appeal` appends an entry with
`status: "under_review"` → the writer gets a confirmation. Nothing is
re-scored and nothing is overwritten.

---

## 2. The two signals

### Signal one — `detector.py` (given)

**What it measures:** how predictable the text is to a small language model
(gpt2), as perplexity — the model's average surprise per token.

**Why that might differ between human and AI writing:** a language model
writes by choosing likely next words, so its output is text a model finds
easy to predict. Humans make odder choices — specific details, abrupt turns,
unusual words — that raise perplexity.

**What it can't see:**

- **Authorship.** It sees predictability, and predictable ≠ machine-written.
  Plain writing — someone writing in a second language, a younger writer,
  anyone using safe vocabulary in short sentences — scores as machine-like as
  machine text does. These are the writers least able to argue back.
- **The reverse:** AI text prompted to be ornate, full of rare words, or run
  through a paraphraser scores *human*, because rare words are exactly what
  the model fails to predict.
- **Anything after ~300 words.** Input is truncated at 400 tokens. A human
  opening paragraph followed by pasted AI text is scored on the human part
  only.
- **Familiar text.** Well-known passages (quotes, famous speeches, boilerplate
  licence text) are predictable because gpt2 has seen them, not because a
  model wrote them.
- **Modern models.** gpt2 is from 2019. Its idea of "predictable" isn't the
  same as what a current model would write.

### Signal two — `stylometry.py` (mine to build)

**What it measures:** the shape of the text with no understanding of its
meaning. My plan for the three measures:

| Measure | Computed as | AI-like direction |
|---|---|---|
| Sentence-length spread | stdev / mean of words per sentence (coefficient of variation); one sentence → treat as "no evidence" (0.5), not as zero spread | **low** spread → AI |
| Vocabulary variety | type-token ratio averaged over fixed 50-word windows, so long and short texts are comparable | **low** variety → AI |
| Punctuation variety | rate of the "interesting" marks — `; : — ( ) ? !` — per 100 words, not full stops and commas | **low** rate → AI |

Each is mapped to 0–1 and flipped so that higher = more AI, then averaged.
Exact mapping gets calibrated in Milestone 4.

**Why that might differ between human and AI writing:** "most likely next
word" produces averages — even, mid-length sentences, a narrow band of safe
vocabulary, tidy punctuation. Human writing is lumpier: a three-word sentence
next to a forty-word one, a dash, a question, a word repeated on purpose.

**What it can't see:**

- **Meaning.** It can't read. Anything that changes the shape without changing
  the substance moves it: adding typos, splitting or merging sentences,
  sprinkling in dashes and question marks, pasting a quotation. These edits
  are cheap and deliberate — exactly what unit 8's attack set does.
- **Writers who are regular on purpose.** Technical writing, instructions,
  bulleted lists and the same plain second-language writer above all look
  "even", so they score AI-like here too.
- **Short text.** Three sentences give a spread of almost nothing; the
  numbers are noise below roughly 100 words.
- **Non-prose.** Poetry, code, lists and dialogue have their own shape that
  none of these measures were designed for.

### What the two blind spots mean together

The signals measure different things, but **they share one blind spot: plain,
regular human writing looks AI-like to both of them.** So when both signals
agree on "AI" for plain writing, that agreement is *not* two independent
pieces of evidence. The combining rule and thresholds have to be built
knowing that.

---

## 3. Tracing the false positive

**Who:** Mai, a first-year student writing in English as a second language,
submits a 220-word reflection she wrote herself. She uses words she's sure of,
short sentences of similar length, and almost no punctuation beyond full stops.

**Through the service, with the placeholder settings in `config.py`
(0.5/0.5 average, AI above 0.65):**

| Step | What happens to Mai's text |
|---|---|
| 1–2 | Valid JSON, valid length. Gets `content_id` `c7e1…`. |
| 3 | gpt2 finds it very predictable — perplexity ~25 → `model_score ≈ 0.72`. |
| 4 | Even sentence lengths, few distinct words per window, no dashes or semicolons → `style_score ≈ 0.68`. |
| 5 | Average → `combined_score ≈ 0.70`. |
| 6 | 0.70 > 0.65 → `guess: "ai"`, labelled high-confidence AI. |
| 7 | Logged as `decided`; the response is returned to her. |

**What the label said to her:** with careless wording, something like
"This text was likely generated by AI" — an accusation, about work she wrote,
from a system she can't question.

**What she can do about it:** `POST /appeal` with her `content_id` and her
reasoning. That moves her item to `under_review` and records her side next to
the original decision. Nothing is re-scored automatically and nothing tells
her who reviews it or when. If she didn't keep the `content_id`, she has
nothing to appeal with.

**What this decides for the build:**

1. **The AI label needs more than "the average is high".** Both signals
   point the wrong way for Mai, so an average is no protection. The AI label
   should need a high combined score *and* both signals clearly high — and
   the threshold for it should sit well above the placeholder 0.65 (I expect
   0.75–0.80, confirmed against a plainly-written human sample in
   Milestone 4). The cost: more lightly-edited AI text lands in "unsure"
   instead of "AI". I accept that trade — a missed detection costs the site
   a little; a wrong accusation costs Mai a lot.
2. **The unsure band is wide on purpose**, and the unsure label must not read
   as a softer accusation.
3. **No label says "you used AI".** Labels describe what the *text* looks
   like to the system, say it can be wrong, and every non-human label tells
   the writer they can appeal and gives them the `content_id` to do it.
4. **The response always returns `content_id`, and `/appeal` gives an
   honest status** — "a person will look at this", not a promise of an
   outcome.
5. **Calibration has to include a plain human sample**, not just "clearly
   human" literary text — otherwise thresholds get tuned on the writers
   least likely to be accused.

---

## 4. Endpoint contracts

Every error response, from either endpoint, has the same shape:

```json
{ "error": "machine_readable_code", "message": "A sentence a person can read." }
```

Every request that's refused is still written to the audit log with
`audit.log_rejection` — a refusal that leaves no trace looks like silence.

### `POST /submit`

**Request** — JSON object, `Content-Type: application/json`

| Field | Type | Required | Rules |
|---|---|---|---|
| `text` | string | yes | Stripped of leading/trailing whitespace; must be at least 1 character after stripping and at most 20,000 characters. |
| `creator_id` | string | yes | Non-empty after stripping, at most 100 characters. Identifies the writer; not verified (no accounts). |

Extra fields are ignored.

**Success — `200 OK`**

| Field | Type | Meaning |
|---|---|---|
| `content_id` | string (UUID4) | Handle for this decision. Needed to appeal. |
| `creator_id` | string | Echoed back. |
| `guess` | `"human"` \| `"unsure"` \| `"ai"` | Machine-readable verdict. |
| `label` | string | The full sentence shown to the writer. |
| `confidence` | float 0–1 | How far `combined_score` sits from the 0.5 coin-flip, scaled: `abs(combined_score − 0.5) × 2`. 0 = no idea, 1 = as sure as the system gets. Not a probability of AI. |
| `combined_score` | float 0–1 | Output of `combine_signals`. Higher = more AI-like. |
| `model_score` | float 0–1 | Signal one. Higher = more AI-like. |
| `style_score` | float 0–1 | Signal two. Higher = more AI-like. |
| `status` | `"decided"` | Lifecycle state. |
| `timestamp` | string (ISO 8601, UTC) | When the decision was made; matches the log entry. |

All floats rounded to 4 decimal places.

```json
{
  "content_id": "c7e1f0a2-5b3d-4e8a-9f61-2d0c8b7a4e19",
  "creator_id": "mai-01",
  "guess": "unsure",
  "label": "We can't tell whether this was written by a person or generated by AI. ...",
  "confidence": 0.24,
  "combined_score": 0.62,
  "model_score": 0.72,
  "style_score": 0.52,
  "status": "decided",
  "timestamp": "2026-10-28T18:04:11+00:00"
}
```

**Errors**

| Status | `error` | When |
|---|---|---|
| `400` | `invalid_json` | Body isn't JSON, or is JSON but not an object. |
| `400` | `missing_text` | `text` absent or not a string. |
| `400` | `empty_text` | `text` is empty or whitespace only. |
| `400` | `missing_creator_id` | `creator_id` absent, not a string, or empty. |
| `413` | `text_too_long` | `text` over 20,000 characters. |
| `422` | `text_too_short` | Too short to score (the detector raises `ValueError` below 3 tokens). |
| `429` | `rate_limited` | Unit 8. Shape already defined in `app.py`. |
| `503` | `detector_unavailable` | The model couldn't load (`DetectorUnavailable`). |

No error ever produces a label. A text that can't be scored is not called
human *or* AI.

### `POST /appeal`

**Request** — JSON object

| Field | Type | Required | Rules |
|---|---|---|---|
| `content_id` | string | yes | Must match a decision in the audit log. |
| `reasoning` | string | yes | The writer's explanation. Non-empty after stripping, at most 5,000 characters. |

The appeal's `creator_id` is taken from the original decision in the log, not
from the request. (Anyone holding a `content_id` can appeal it; an appeal only
asks for review, so that's acceptable without accounts.)

**Success — `200 OK`**

| Field | Type | Meaning |
|---|---|---|
| `content_id` | string | The decision being appealed. |
| `status` | `"under_review"` | New lifecycle state. |
| `original_guess` | string | What the system said. |
| `original_label` | string | The exact sentence the writer saw. |
| `message` | string | Plain confirmation for the writer: received, a person will review it, nothing about the original decision has been treated as final. |
| `timestamp` | string (ISO 8601, UTC) | When the appeal was recorded. |

```json
{
  "content_id": "c7e1f0a2-5b3d-4e8a-9f61-2d0c8b7a4e19",
  "status": "under_review",
  "original_guess": "ai",
  "original_label": "...",
  "message": "Thanks — your appeal is recorded and this piece is now waiting for a person to review it.",
  "timestamp": "2026-10-28T18:09:40+00:00"
}
```

**Errors**

| Status | `error` | When |
|---|---|---|
| `400` | `invalid_json` | Body isn't a JSON object. |
| `400` | `missing_content_id` | `content_id` absent, not a string, or empty. |
| `400` | `missing_reasoning` | `reasoning` absent, not a string, or empty. |
| `413` | `reasoning_too_long` | `reasoning` over 5,000 characters. |
| `404` | `unknown_content_id` | No decision with that id in the log. |
| `409` | `already_under_review` | The item already has an appeal. The log is append-only; a second appeal adds nothing a reviewer needs. |

---

## Read-back check

Could someone build against this without asking me a question? The points I
had to settle to say yes: the direction of every score (higher = AI, always);
what `confidence` means and how it's computed; what happens on each bad
input, including text too short to score; where the appeal's `creator_id`
comes from; and what a second appeal does. The one thing deliberately left
open is the exact thresholds and label wording — those are Milestones 4 and 5,
and section 3 sets the rule they have to follow.
