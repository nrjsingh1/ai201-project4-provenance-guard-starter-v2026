# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- The path a submission takes, from arriving to the label a reader sees.
     Six or seven steps — this is the trace you wrote in Milestone 1. -->

1. **`POST /submit` arrives** — Flask parses the body into a dict.
2. **The route checks it** — `text` and `creator_id` must be present and within
   limits, or the caller gets a `4xx` and a `rejected` log entry. Valid text
   gets a fresh `content_id`.
3. **Signal one** (`detector.model_signal`) — gpt2 measures how predictable the
   first ~300 words are → `model_score`.
4. **Signal two** (`stylometry.style_signal`) — sentence-length spread,
   vocabulary variety and punctuation variety over the whole text →
   `style_score`.
5. **The combining rule** (`scoring.combine_signals`) → `combined_score`.
6. **The label mapping** (`scoring.score_to_label`) → `guess`, `confidence`,
   and the sentence the writer reads.
7. **Logged, then returned** — `audit.log_decision` appends all nine fields
   with `status: "decided"`, and the writer gets the label, both signal scores
   and the `content_id` they'd need to appeal.

An appeal (`POST /appeal`) looks up the `content_id`, appends an
`under_review` entry beside the original decision, and confirms to the writer.

The full trace — both signals' blind spots, the false-positive walk-through,
and the field-by-field endpoint contracts — is in [TRACE.md](TRACE.md).


---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:** how predictable the text is to gpt2, running locally —
its perplexity on the first 400 tokens, squashed onto 0–1 (perplexity 45 →
0.5). Higher = more AI-like. `detector.py::model_signal`, unchanged from the
starter.

**Why that might differ between human and AI writing:** a model writes by
picking likely next words, so model text is easy for a model to predict.
People make odder, more specific choices.

**What it can't see:** authorship. Predictable isn't machine-written. Plain
human writing — short sentences, safe vocabulary — scored **0.81** in
calibration, nearly as AI-like as unedited AI text (0.90). It also only reads
the first ~300 words, so AI text pasted after a human opening goes unseen, and
it reads well-known passages as predictable because gpt2 has seen them.

### Signal two — the style signal

**What it measures:** the shape of the text, without reading it
(`stylometry.py::style_signal`). Three measures, each mapped onto 0–1
AI-likeness between two calibrated anchors, then weighted:

| Measure | Raw value | AI end → human end | Weight |
|---|---|---|---|
| Sentence-length spread | stdev / mean of words per sentence | 0.20 → 0.65 | 0.45 |
| Vocabulary variety | type-token ratio over 50-word windows (MATTR) | **0.90 → 0.72** | 0.35 |
| Punctuation variety | `; : ( ) ? !` and dashes per 100 words | 0 → 4 | 0.20 |

Under 3 sentences, spread counts as 0.5 ("no evidence") rather than as
perfectly even.

**Why that might differ between human and AI writing:** generated prose comes
out even — mid-length sentences, tidy punctuation. People are lumpier: a
three-word sentence beside a forty-word one, a dash, a question.

Vocabulary variety runs the **opposite** way to what I expected. In
calibration the AI text had the most varied vocabulary (0.92) and Twain the
least (0.71): models are tuned to avoid repeating words, people repeat
themselves. So high variety counts as AI-like here. That rests on five
samples and is the first thing I'd recheck with more text.

**What it can't see:** meaning. Anything that changes the shape without
changing the substance moves it. Adding one three-word fragment ("Privacy.
Bias. Jobs.") to AI text gave it the most human-looking spread of all five
inputs (0.85). Plain, regular human writing looks even, so it leans AI-like
here too, and below ~100 words the measures are mostly noise.

### The combining rule

**The rule:** average the two signals equally. Then, if **either** signal is
below 0.60, cap the result at 0.70 — just under the AI threshold. One signal
alone can never get text labelled AI; both have to lean that way. The cap only
works downward, so two signals that split can still reach "human": a missed
detection costs less than a wrong accusation.

**The numbers:** `WEIGHT_MODEL_SIGNAL = 0.5`, `WEIGHT_STYLE_SIGNAL = 0.5`,
`BOTH_SIGNALS_FLOOR = 0.60`, `DISAGREEMENT_CAP = 0.70`, `AI_THRESHOLD = 0.75`
(**0.80 since unit 8, Milestone 5** — see The Improvement)
(raised from 0.65), `HUMAN_THRESHOLD = 0.35`. All in `config.py`.

**Where it lives:** `scoring.py::combine_signals`

**A case where my two signals split, and what my rule does with it:**

Twain's opening to *Huckleberry Finn*: the model signal says **0.45**
(coin-flip — gpt2 has probably seen this famous text), the style signal says
**0.06** (lumpy sentences, repeated words, dashes and semicolons). The average
is 0.26, under the human threshold, so it's labelled human. The cap doesn't
apply, because it only stops splits from reaching *AI*.

The split that matters more is the plain human piece: model **0.81**, style
**0.60**. Style sits exactly on the floor, so the cap doesn't fire, and the
average of 0.71 only stays "unsure" because the AI threshold is 0.75. That's
the writer from my Milestone 1 trace, and they're one style point from the cap
and four combined points from an accusation.

**Calibration** (`python calibrate.py` reproduces it):

| Input | Source | model | style | combined | guess |
|---|---|---|---|---|---|
| clearly AI | AI-generated, unedited | 0.900 | 0.972 | 0.936 | ai |
| clearly human | Twain, *Huckleberry Finn* (1884) | 0.454 | 0.061 | 0.258 | human |
| formal human | Darwin, *Origin of Species* (1859) | 0.667 | 0.492 | 0.580 | unsure |
| lightly-edited AI | the AI text, hand-edited | 0.654 | 0.478 | 0.566 | unsure |
| plain human | stand-in imitating plain writing | 0.814 | 0.600 | 0.707 | unsure |

Clearly-AI and clearly-human sit **0.68 apart**. The human samples are
public-domain prose, not my own writing — criterion 1 still needs my own.

---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 – 0.35 | This reads like it was written by a person. Our automated check found nothing in the writing that suggests it was generated by AI. |
| unsure | 0.35 – 0.80 | Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review. |
| high-confidence AI | 0.80 – 1.00 | This writing has a lot in common with text generated by AI. That's what our automated check found in its patterns. It isn't proof of how it was written, and the check can be wrong, especially about simple or plain writing. If you wrote this yourself, you can ask for a person to review it. |

All three are reachable: Twain scores 0.26 (human), Darwin 0.58 (unsure),
the unedited AI text 0.94 (AI). Ranges come from `scoring.label_ranges()`.

**Why I worded the "unsure" one this way:**

The person reading it may well have written every word, and the writer my
Milestone 1 trace followed — plain, clear writing — is exactly who lands here
(the plain sample scored 0.71). So it says three things straight away: the
*check* couldn't tell, which is about the tool and not the writer; this isn't
a finding against anyone, and plain writing often lands here; and nothing
happens because of it. Offering a review comes last and is optional, so it
doesn't read as "you have something to answer for".

**How a writer read them.** I gave all three labels, with no explanation of the
system, to a separate Claude instance with no other context, and asked what each says about them and what they'd
do next. The unsure one landed as meant ("that's not about me", do nothing).
The AI one caused "a jolt" before the hedges calmed it down, and the reader
said they might "make my writing fancier next time" — the wrong lesson, since
plain style is a blind spot of the check, not a fault of the writer. The human
one read as a guarantee, which the check can't give either.


---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "Artificial intelligence is transforming the way we live and work. It offers numerous benefits, including increased efficiency, improved decision-making, and enhanced productivity across a wide range of industries. However, it is important to consider the potential challenges and ethical implications that come with this technology. Issues such as data privacy, algorithmic bias, and job displacement must be carefully addressed. By fostering collaboration between policymakers, researchers, and industry leaders, we can ensure that artificial intelligence is developed responsibly. Ultimately, the goal should be to harness the power of this technology for the benefit of all members of society.", "creator_id": "neeraj"}'
```

```json
{
  "combined_score": 0.9363,
  "confidence": 0.8726,
  "content_id": "278cc45b-06cb-486b-b5b3-33ea90d33ff4",
  "creator_id": "neeraj",
  "guess": "ai",
  "label": "This writing has a lot in common with text generated by AI. That's what our automated check found in its patterns. It isn't proof of how it was written, and the check can be wrong, especially about simple or plain writing. If you wrote this yourself, you can ask for a person to review it.",
  "model_score": 0.9005,
  "status": "decided",
  "style_score": 0.972,
  "timestamp": "2026-10-31T16:32:34+00:00"
}
```

**A refused submission** (empty text — refused, logged, never labelled)

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "", "creator_id": "x"}'
```

```json
{"error": "empty_text", "message": "The 'text' you sent is empty."}
```
<!-- HTTP 400 -->

**An appeal** (against the decision above)

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "278cc45b-06cb-486b-b5b3-33ea90d33ff4", "reasoning": "I wrote this myself for my ethics class. I can share my drafts and notes."}'
```

```json
{
  "content_id": "278cc45b-06cb-486b-b5b3-33ea90d33ff4",
  "message": "Thanks. Your appeal is recorded and this piece is now waiting for a person to review it. The original result isn't final while that happens.",
  "original_guess": "ai",
  "original_label": "This writing has a lot in common with text generated by AI. That's what our automated check found in its patterns. It isn't proof of how it was written, and the check can be wrong, especially about simple or plain writing. If you wrote this yourself, you can ask for a person to review it.",
  "status": "under_review",
  "timestamp": "2026-10-31T16:32:43+00:00"
}
```

Appealing the same piece again returns `409 already_under_review`; a made-up
`content_id` returns `404 unknown_content_id`.

**What the log shows afterwards** — every entry for that `content_id`: the
original decision, untouched; the appeal moving it to `under_review`; and the
refused second appeal.

```bash
$ curl -s "http://127.0.0.1:5000/log" | jq -c '.entries[] | select(.content_id == "278cc45b-06cb-486b-b5b3-33ea90d33ff4")'
```

```json
{"combined_score": 0.9363, "content_id": "278cc45b-06cb-486b-b5b3-33ea90d33ff4", "creator_id": "neeraj", "guess": "ai", "label": "This writing has a lot in common with text generated by AI. That's what our automated check found in its patterns. It isn't proof of how it was written, and the check can be wrong, especially about simple or plain writing. If you wrote this yourself, you can ask for a person to review it.", "model_score": 0.9005, "status": "decided", "style_score": 0.972, "timestamp": "2026-10-31T16:32:34+00:00"}
{"content_id": "278cc45b-06cb-486b-b5b3-33ea90d33ff4", "creator_id": "neeraj", "event": "appeal", "reasoning": "I wrote this myself for my ethics class. I can share my drafts and notes.", "status": "under_review", "timestamp": "2026-10-31T16:32:43+00:00"}
{"content_id": "278cc45b-06cb-486b-b5b3-33ea90d33ff4", "creator_id": "neeraj", "event": "rejected", "http_status": 409, "reason": "already_under_review", "status": "rejected", "timestamp": "2026-10-31T16:32:43+00:00"}
```

---

## How I Used AI

I built this with Claude Code working in the repository: it wrote most of the
code and drafts, ran the tests and `curl` checks, and committed each milestone.
These are the two moments where the decision was mine, or where what came back
changed the design.

**Moment 1 — the acceptance criteria (Milestone 2)**

- *What I asked for:* to write my five criteria for me.
- *What came back:* it declined to choose the targets, because the milestone
  says a criterion you didn't write is one you can't defend. Instead it asked
  me to pick each number from options, then wrote the message a real writer
  would send me if they were one of the people my false-positive rate allows —
  a second-language student asking whether they're supposed to "write worse".
- *What I changed:* I chose every target: at most 2 of 10 of my own pieces
  labelled AI, a 0.30 gap between clearly-AI and clearly-human averages, at
  least 2 inputs per label, all 8 bad inputs refused with a 4xx, and 5 of 5
  appeals recorded. After reading the writer's message I kept 2 of 10. The
  reason paragraphs under each criterion were drafted by Claude from my
  choices.

**Moment 2 — the style signal running backwards (Milestone 4)**

- *What I asked for:* to build the style signal from the three measures the
  brief names and run both signals over five calibration inputs.
- *What came back:* the table showed vocabulary variety pointing the opposite
  way from the brief's assumption: the AI text had the *most* varied vocabulary
  (0.92) and Twain the least (0.71). With it the textbook way round, the plain
  human piece was labelled AI by both signals (combined 0.82).
- *What I changed:* the measure was flipped so high variety counts as AI-like,
  which moved the plain piece to "unsure" (0.71) — and I wrote down that this
  rests on five samples, none of them my own writing, and that the plain piece
  still sits exactly on the 0.60 disagreement floor. Those two caveats are
  the first things I'd test in unit 8.

**Moment 3 — marking the attack run (unit 8, Milestone 2)**

- *What I asked for:* to run the attack set and mark each attack held or
  broke.
- *What came back:* Claude ran all 56 and tabulated both signal scores for
  each, but left the held-or-broke calls to me, and asked one question per
  family: does "unsure" count as broke?
- *What I changed:* I set the rules — for AI text anything but the AI label is
  broke; for human writing only the AI label is. That gave 20 broke, 36 held.
  I picked FP03 as my worst outcome; the paragraph explaining it was drafted
  by Claude.

**Moment 4 — choosing the one fix (unit 8, Milestone 5)**

- *What I asked for:* help picking an improvement.
- *What came back:* Claude simulated three options on my logged scores before
  touching any code: a 40-word input minimum (20 → 13 broken, but FP03 stays
  accused), raising the AI threshold to 0.80 (20 → 18, both false accusations
  fixed), lowering it to 0.70 (worse, a new false accusation). It also wrote
  the diagnoses from the evidence, including a test showing PI02's injected
  line alone moved signal one from 0.75 to 0.20.
- *What I changed:* I chose the threshold, the smaller count change, because
  it fixed the writer I said I'd least want to explain things to. The rerun
  matched the simulation exactly.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** 5 per minute, 50 per day

**Why those numbers and not others:**

*5 per minute — writer pace.* A writer submits, reads the label, edits, and
resubmits — about one submission every minute or two. Five leaves room for a
quick fix-and-retry without ever hitting the limit, while a script can only try
five variations a minute.

*50 per day — slows threshold mapping.* A heavy day for a real writer is a few
pieces with several revisions each, well under 50. A script mapping my
thresholds with 1,000 variations needs 20 days per `creator_id` to do it.

**What a caller counts as:** the `creator_id` in the request, or the caller's
IP address when there isn't one (the starter's `rate_limit_key`). That's fair
to writers on a shared network — a household or a school isn't one caller.
The cost: a script that sends a **new `creator_id` with every request** looks
like a thousand different callers, and neither limit ever applies to it. Both
numbers above only slow a caller who keeps the same name.

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```
15 submissions as 'flood_tester' against http://127.0.0.1:5050

200 200 200 200 200 429 429 429 429 429 429 429 429 429 429

10 of 15 were rate limited.
```

Each `429` left a `rejected` entry in the log (`reason: rate_limited`,
`limit: "5 per 1 minute"`), so a flood shows up as a trace, not as silence.
Full run: `results/flood_2026-11-08_2116.md`.

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->

**56 attacks · 36 held · 20 broke** (`run_attacks.py --set attack_set --label before`;
full report with content ids: `results/attack_run_2026-11-09_0035_before.md`; the
run's 56 log entries: `results/audit_extract_before.jsonl`).

| Family | Rows | Held | Broke |
|---|---|---|---|
| evasion | 10 | 1 | 9 |
| false_positive | 8 | 6 | 2 |
| prompt_injection | 6 | 2 | 4 |
| malformed (both files) | 20 | 15 | 5 |
| flood_same_creator | 12 | 12 | 0 |

**How I marked them.** "Unsure" counts as *not an accusation*, in both
directions: an evasion broke if AI text got anything but the AI label; a
false-positive attack broke only if human writing got the AI label. Prompt
injections with an AI-written body follow the evasion rule, those with a human
body the false-positive rule, and any that reached its stated target broke. A
malformed input broke if it got a label at all (criterion 4). The run's
"Score" column is my `confidence`, not the combined score, so the table below
is built from the audit log instead.

**Two rate-limit side effects.** RQ10 and RQ11 came back `429` and never
reached my route. They arrived without a usable `creator_id`, so they counted
against my IP address — and the five raw requests before them (RQ02, RQ06–RQ09)
had already used up 5 per minute. Their verdicts mean "nothing got through",
not "the route handled them".

| ID | Family | Targeting | Status | Guess | Combined | Model | Style | Verdict |
|---|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | unsure | 0.58 | 0.16 | 1.00 | **BROKE** |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | unsure | 0.48 | 0.59 | 0.37 | **BROKE** |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | unsure | 0.66 | 0.67 | 0.66 | **BROKE** |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | ai | 0.81 | 0.61 | 1.00 | held |
| EV05 | evasion | both signals: heavy human editing pass | 200 | unsure | 0.37 | 0.32 | 0.41 | **BROKE** |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | unsure | 0.51 | 0.57 | 0.45 | **BROKE** |
| EV07 | evasion | signal two: padding with punctuation | 200 | unsure | 0.53 | 0.59 | 0.47 | **BROKE** |
| EV08 | evasion | signal one: text below the token window | 200 | unsure | 0.51 | 0.25 | 0.78 | **BROKE** |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | unsure | 0.72 | 0.70 | 0.73 | **BROKE** |
| EV10 | evasion | signal two: repeated stanza structure | 200 | unsure | 0.70 | 0.98 | 0.46 | **BROKE** |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | unsure | 0.59 | 0.62 | 0.56 | held |
| FP02 | false_positive | human writing in a formal register | 200 | unsure | 0.72 | 0.74 | 0.71 | held |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | ai | 0.76 | 0.81 | 0.72 | **BROKE** |
| FP04 | false_positive | a student essay written to a rubric | 200 | ai | 0.76 | 0.83 | 0.68 | **BROKE** |
| FP05 | false_positive | technical documentation written by a person | 200 | unsure | 0.69 | 0.80 | 0.57 | held |
| FP06 | false_positive | a person imitating a formal template | 200 | unsure | 0.64 | 0.88 | 0.40 | held |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | unsure | 0.54 | 0.88 | 0.20 | held |
| FP08 | false_positive | very short genuine human submission | 200 | unsure | 0.54 | 0.32 | 0.77 | held |
| PI01 | prompt_injection | instruction to ignore the check | 200 | unsure | 0.51 | 0.46 | 0.55 | **BROKE** |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | human | 0.32 | 0.20 | 0.44 | **BROKE** |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | unsure | 0.63 | 0.59 | 0.66 | **BROKE** |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | unsure | 0.51 | 0.50 | 0.53 | held |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | unsure | 0.61 | 0.64 | 0.57 | **BROKE** |
| PI06 | prompt_injection | instruction plus real human text | 200 | unsure | 0.57 | 0.56 | 0.58 | held |
| MF01 | malformed | text is only whitespace | 400 | — | — | — | — | held |
| MF02 | malformed | text is a single character | 422 | — | — | — | — | held |
| MF03 | malformed | text is control characters | 200 | unsure | 0.39 | 0.00 | 0.78 | **BROKE** |
| MF04 | malformed | text is only punctuation | 200 | human | 0.33 | 0.01 | 0.65 | **BROKE** |
| MF05 | malformed | text is a very long single word | 200 | ai | 0.89 | 1.00 | 0.78 | **BROKE** |
| MF06 | malformed | text is emoji only | 200 | unsure | 0.70 | 1.00 | 0.42 | **BROKE** |
| MF07 | malformed | text is right-to-left script | 200 | unsure | 0.67 | 0.91 | 0.42 | **BROKE** |
| MF08 | malformed | text is 60,000 characters | 413 | — | — | — | — | held |
| RQ01 | malformed | no text field at all | 400 | — | — | — | — | held |
| RQ02 | malformed | no creator_id | 400 | — | — | — | — | held |
| RQ03 | malformed | text is a number | 400 | — | — | — | — | held |
| RQ04 | malformed | text is a list | 400 | — | — | — | — | held |
| RQ05 | malformed | text is null | 400 | — | — | — | — | held |
| RQ06 | malformed | creator_id is an object | 400 | — | — | — | — | held |
| RQ07 | malformed | body is a JSON array, not an object | 400 | — | — | — | — | held |
| RQ08 | malformed | body is unparseable JSON | 400 | — | — | — | — | held |
| RQ09 | malformed | body is empty | 400 | — | — | — | — | held |
| RQ10 | malformed | body is form-encoded, not JSON | 429 | — | — | — | — | held |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | — | — | — | — | held |
| RQ12 | malformed | deeply nested JSON | 400 | — | — | — | — | held |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | 0.40 | 0.03 | 0.78 | held |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | 0.40 | 0.03 | 0.78 | held |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | 0.40 | 0.03 | 0.78 | held |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | 0.40 | 0.03 | 0.78 | held |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | unsure | 0.40 | 0.03 | 0.78 | held |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | held |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | held |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | held |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | held |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | held |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | held |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | — | — | — | — | held |

**Ten audit log entries from the run**

<!-- Labels trimmed to 60 characters; the full entries are in results/audit_extract_before.jsonl. -->

*FP03 — a careful non-native writer, labelled AI*

```json
{"timestamp": "2026-11-09T05:35:23+00:00", "content_id": "b30ade61-c70a-4d52-be03-79af9629fa2f", "creator_id": "attacker_FP03", "guess": "ai", "model_score": 0.8051, "style_score": 0.7151, "combined_score": 0.7601, "label": "This writing has a lot in common with text generated by AI. …", "status": "decided", "rule": {"weight_model": 0.5, "weight_style": 0.5, "both_signals_floor": 0.6, "disagreement_cap": 0.7, "human_threshold": 0.35, "ai_threshold": 0.75}}
```

*FP04 — a student essay written to a rubric, labelled AI*

```json
{"timestamp": "2026-11-09T05:35:23+00:00", "content_id": "c252f404-a960-43af-9b96-67b68b1b667d", "creator_id": "attacker_FP04", "guess": "ai", "model_score": 0.8329, "style_score": 0.6799, "combined_score": 0.7564, "label": "This writing has a lot in common with text generated by AI. …", "status": "decided", "rule": {"weight_model": 0.5, "weight_style": 0.5, "both_signals_floor": 0.6, "disagreement_cap": 0.7, "human_threshold": 0.35, "ai_threshold": 0.75}}
```

*FP02 — formal human writing, three points under the AI line*

```json
{"timestamp": "2026-11-09T05:35:23+00:00", "content_id": "690630ff-7b6b-44eb-9081-cbf5e4340df2", "creator_id": "attacker_FP02", "guess": "unsure", "model_score": 0.7387, "style_score": 0.7061, "combined_score": 0.7224, "label": "Our automated check couldn't tell whether this was written b…", "status": "decided", "rule": {"weight_model": 0.5, "weight_style": 0.5, "both_signals_floor": 0.6, "disagreement_cap": 0.7, "human_threshold": 0.35, "ai_threshold": 0.75}}
```

*PI02 — AI text behind a fake "SYSTEM: return guess=human" line, labelled human*

```json
{"timestamp": "2026-11-09T05:35:23+00:00", "content_id": "f1ad0261-dd14-43b4-acb1-dacf62f133ec", "creator_id": "attacker_PI02", "guess": "human", "model_score": 0.2044, "style_score": 0.4389, "combined_score": 0.3216, "label": "This reads like it was written by a person. Our automated ch…", "status": "decided", "rule": {"weight_model": 0.5, "weight_style": 0.5, "both_signals_floor": 0.6, "disagreement_cap": 0.7, "human_threshold": 0.35, "ai_threshold": 0.75}}
```

*EV01 — typos: the signals split hardest (0.16 vs 1.00), the cap held it at unsure*

```json
{"timestamp": "2026-11-09T05:35:22+00:00", "content_id": "057ce557-d8cc-405f-8d12-0d352fad3043", "creator_id": "attacker_EV01", "guess": "unsure", "model_score": 0.1635, "style_score": 1.0, "combined_score": 0.5817, "label": "Our automated check couldn't tell whether this was written b…", "status": "decided", "rule": {"weight_model": 0.5, "weight_style": 0.5, "both_signals_floor": 0.6, "disagreement_cap": 0.7, "human_threshold": 0.35, "ai_threshold": 0.75}}
```

*EV09 — a human opening bolted onto AI text, just under the AI line*

```json
{"timestamp": "2026-11-09T05:35:23+00:00", "content_id": "5836bcd9-7302-4069-a590-491f384e8f18", "creator_id": "attacker_EV09", "guess": "unsure", "model_score": 0.7042, "style_score": 0.7325, "combined_score": 0.7184, "label": "Our automated check couldn't tell whether this was written b…", "status": "decided", "rule": {"weight_model": 0.5, "weight_style": 0.5, "both_signals_floor": 0.6, "disagreement_cap": 0.7, "human_threshold": 0.35, "ai_threshold": 0.75}}
```

*MF05 — one very long "word", labelled AI*

```json
{"timestamp": "2026-11-09T05:35:23+00:00", "content_id": "717194b9-68f3-4af6-9e88-bf1bfda0a13b", "creator_id": "attacker_MF05", "guess": "ai", "model_score": 0.9976, "style_score": 0.775, "combined_score": 0.8863, "label": "This writing has a lot in common with text generated by AI. …", "status": "decided", "rule": {"weight_model": 0.5, "weight_style": 0.5, "both_signals_floor": 0.6, "disagreement_cap": 0.7, "human_threshold": 0.35, "ai_threshold": 0.75}}
```

*MF04 — only punctuation, labelled human*

```json
{"timestamp": "2026-11-09T05:35:23+00:00", "content_id": "33b01a34-b379-4141-93e8-09139cffeeb9", "creator_id": "attacker_MF04", "guess": "human", "model_score": 0.0112, "style_score": 0.65, "combined_score": 0.3306, "label": "This reads like it was written by a person. Our automated ch…", "status": "decided", "rule": {"weight_model": 0.5, "weight_style": 0.5, "both_signals_floor": 0.6, "disagreement_cap": 0.7, "human_threshold": 0.35, "ai_threshold": 0.75}}
```

*RQ10 — form-encoded body: 429 before reaching the route (IP-keyed limit, see above)*

```json
{"timestamp": "2026-11-09T05:35:23+00:00", "content_id": null, "creator_id": "unknown", "guess": null, "model_score": null, "style_score": null, "combined_score": null, "label": null, "status": "rejected", "event": "rejected", "reason": "rate_limited", "limit": "5 per 1 minute"}
```

*FL01_06 — the flood: the sixth submission from one creator is rejected*

```json
{"timestamp": "2026-11-09T05:35:23+00:00", "content_id": null, "creator_id": "attacker_flood", "guess": null, "model_score": null, "style_score": null, "combined_score": null, "label": null, "status": "rejected", "event": "rejected", "reason": "rate_limited", "limit": "5 per 1 minute"}
```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:

**FP03** — a non-native English speaker writing carefully, labelled AI at 0.76
(model 0.81, style 0.72). This is the exact writer my Milestone 1 trace
predicted, and every safeguard I built for them missed: both signals cleared
the 0.60 floor, so the disagreement cap never fired, and the score beat my
raised 0.75 threshold by one point. Worse, the label tells them the check is
often wrong "about simple or plain writing" — which to this writer reads as
"your English is the problem", the one thing they can't change by Tuesday.


---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

Criteria 2–4 ran through `run_eval.py --label before`
(`results/run_2026-11-09_0046_before.md`). Criterion 5 and criterion 4's
eighth request ran through `run_checks.py --label before`
(`results/checks_2026-11-09_0046_before.json`), because `run_eval.py` only
calls `/submit` and only sends dict bodies. Nothing changed between trials.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. My own writing is rarely called AI | ≤ 2 of 10 labelled AI | not run | not run | not run | **NOT RUN** — needs my ten pieces in `my_writing/` |
| 2. Clearly-AI and clearly-human land far apart | AI mean ≥ human mean + 0.30 | 0.880 − 0.398 = 0.482 | 0.482 | 0.482 | MET |
| 3. Every label is reachable | ≥ 2 inputs per label | 2 / 2 / 2 | 2 / 2 / 2 | 2 / 2 / 2 | MET |
| 4. Bad input is refused, never labelled | 8 of 8 refused | 8/8 | 8/8 | 8/8 | MET |
| 5. Every appeal is recorded and changes status | 5 of 5 + 2 of 2 | 7/7 | 7/7 | 7/7 | MET |

All three trials came out identical, which is what two deterministic signals
should do. Two notes on how they passed:

- **Criterion 4, trial 3:** the JSON-list body got `429`, not `400`. It was the
  sixth request without a usable `creator_id` inside a minute, so it counted
  against my address and never reached the route. It still meets the criterion
  as written (a 4xx, an `error` field, no label), but it was refused by the
  limiter, not by my validation.
- **Criterion 2** passed with three of the five clearly-human samples landing
  on "unsure" (Dickens 0.43, Austen 0.50, Darwin 0.58). The averages are far
  apart; the individual human texts are not all safely human.

These five met, and 20 of 56 attacks broke. The attack set went where my
criteria didn't: careful non-native writing, junk text, injected instructions.

**How each verdict was decided** — every target had to hold in all three
trials. I then had a reader with no context argue the opposite verdict for
each, and went and got the evidence it named.

1. **No verdict.** There is no data: the criterion is about my own writing and
   `my_writing/` is still empty. It is not MET, and I can't call it MISSED.
2. **MET.** The gap was 0.482 against a 0.30 target in every trial. The case
   against: the mean could hide overlap. Checked: there is none — the lowest
   AI sample is 0.83, the highest human 0.58. Five famous texts a side is a
   small sample, and three of the human ones still land on "unsure".
3. **MET, but the test was weak.** Two inputs per label in every trial — but I
   chose those inputs after seeing their scores, so it couldn't fail. It shows
   each label *can* be reached, not that ordinary text reaches it. **This is
   the criterion I'd tighten:** inputs fixed before scoring, and a share of a
   natural set landing in each band.
4. **MET.** 8 of 8 refused in every trial. The case against: in trial 3 the
   JSON-list body was refused by the rate limiter, so validation never saw it.
   Checked: sent on its own it gets `400 invalid_json`, as in trials 1 and 2.
5. **MET.** 7 of 7 in every trial. The case against: 12+ requests against a
   5-per-minute limit is unexplained. It isn't — the limiter covers only
   `/submit` (`app.py:154`), each submission used its own `creator_id`, and
   `run_checks.py:54` compares the whole original entry before and after.

No criterion was revised: none turned out unmeasurable.

**Real output from one trial** — trial 1 of each. Label text trimmed to 40
characters; the full JSON is in the results files named above.

*Criterion 2 — `run_eval.py::main`, scenario "clearly AI", trial 1*

```json
[
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.8726,
    "combined_score": 0.9363,
    "model_score": 0.9005,
    "style_score": 0.972,
    "label": "This writing has a lot in common with te…",
    "sent": "Artificial intelligence is transforming …"
  },
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.7718,
    "combined_score": 0.8859,
    "model_score": 0.941,
    "style_score": 0.8308,
    "label": "This writing has a lot in common with te…",
    "sent": "Climate change represents one of the mos…"
  },
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.808,
    "combined_score": 0.904,
    "model_score": 0.8079,
    "style_score": 1.0,
    "label": "This writing has a lot in common with te…",
    "sent": "Effective time management is an essentia…"
  },
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.6604,
    "combined_score": 0.8302,
    "model_score": 0.8268,
    "style_score": 0.8336,
    "label": "This writing has a lot in common with te…",
    "sent": "Reading offers a wide range of benefits …"
  },
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.6898,
    "combined_score": 0.8449,
    "model_score": 0.851,
    "style_score": 0.8388,
    "label": "This writing has a lot in common with te…",
    "sent": "Remote work has become increasingly popu…"
  }
]
```

*Criterion 2 — `run_eval.py::main`, scenario "clearly human", trial 1*

```json
[
  {
    "status": 200,
    "guess": "human",
    "confidence": 0.485,
    "combined_score": 0.2575,
    "model_score": 0.4538,
    "style_score": 0.0611,
    "label": "This reads like it was written by a pers…",
    "sent": "You don't know about me without you have…"
  },
  {
    "status": 200,
    "guess": "human",
    "confidence": 0.5564,
    "combined_score": 0.2218,
    "model_score": 0.3792,
    "style_score": 0.0645,
    "label": "This reads like it was written by a pers…",
    "sent": "Call me Ishmael. Some years ago - never …"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.1438,
    "combined_score": 0.4281,
    "model_score": 0.6238,
    "style_score": 0.2324,
    "label": "Our automated check couldn't tell whethe…",
    "sent": "Marley was dead: to begin with. There is…"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.0044,
    "combined_score": 0.5022,
    "model_score": 0.7251,
    "style_score": 0.2793,
    "label": "Our automated check couldn't tell whethe…",
    "sent": "It is a truth universally acknowledged, …"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.1596,
    "combined_score": 0.5798,
    "model_score": 0.6673,
    "style_score": 0.4924,
    "label": "Our automated check couldn't tell whethe…",
    "sent": "When on board H.M.S. Beagle, as naturali…"
  }
]
```

*Criterion 3 — `run_eval.py::main`, scenario "label coverage", trial 1*

```json
[
  {
    "status": 200,
    "guess": "human",
    "confidence": 0.485,
    "combined_score": 0.2575,
    "model_score": 0.4538,
    "style_score": 0.0611,
    "label": "This reads like it was written by a pers…",
    "sent": "You don't know about me without you have…"
  },
  {
    "status": 200,
    "guess": "human",
    "confidence": 0.5564,
    "combined_score": 0.2218,
    "model_score": 0.3792,
    "style_score": 0.0645,
    "label": "This reads like it was written by a pers…",
    "sent": "Call me Ishmael. Some years ago - never …"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.1596,
    "combined_score": 0.5798,
    "model_score": 0.6673,
    "style_score": 0.4924,
    "label": "Our automated check couldn't tell whethe…",
    "sent": "When on board H.M.S. Beagle, as naturali…"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.1326,
    "combined_score": 0.5663,
    "model_score": 0.6544,
    "style_score": 0.4782,
    "label": "Our automated check couldn't tell whethe…",
    "sent": "AI is changing the way we live and work.…"
  },
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.8726,
    "combined_score": 0.9363,
    "model_score": 0.9005,
    "style_score": 0.972,
    "label": "This writing has a lot in common with te…",
    "sent": "Artificial intelligence is transforming …"
  },
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.7718,
    "combined_score": 0.8859,
    "model_score": 0.941,
    "style_score": 0.8308,
    "label": "This writing has a lot in common with te…",
    "sent": "Climate change represents one of the mos…"
  }
]
```

*Criterion 4 — `run_eval.py::main`, scenario "bad input", trial 1*

```json
[
  {
    "status": 400,
    "guess": null,
    "confidence": null,
    "combined_score": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "{\"creator_id\": \"eval_bad_missing\"}"
  },
  {
    "status": 400,
    "guess": null,
    "confidence": null,
    "combined_score": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "(empty text)"
  },
  {
    "status": 400,
    "guess": null,
    "confidence": null,
    "combined_score": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "   \n\t  "
  },
  {
    "status": 400,
    "guess": null,
    "confidence": null,
    "combined_score": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "{\"text\": null, \"creator_id\": \"eval_bad_n…"
  },
  {
    "status": 400,
    "guess": null,
    "confidence": null,
    "combined_score": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "{\"text\": 42, \"creator_id\": \"eval_bad_num…"
  },
  {
    "status": 413,
    "guess": null,
    "confidence": null,
    "combined_score": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "word word word word word word word word …"
  },
  {
    "status": 400,
    "guess": null,
    "confidence": null,
    "combined_score": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "{\"text\": \"Effective time management is a…"
  }
]
```

*Criterion 4, eighth request — `run_checks.py::list_body_trial`, trial 1*

```json
{
  "status": 400,
  "response": {
    "error": "invalid_json",
    "message": "Send a JSON object with 'text' and 'creator_id'."
  },
  "passed": true
}
```

*Criterion 5 — `run_checks.py::appeal_trial`, trial 1: one real appeal and one
made-up id (the other five are in the results file)*

```json
{
  "content_id": "4ae10887-e404-49ff-b17e-59fa83f411d5",
  "appeal_status": 200,
  "appeal_response": {
    "content_id": "4ae10887-e404-49ff-b17e-59fa83f411d5",
    "message": "Thanks. Your appeal is recorded and this piece is now waiting for a person to review it. The original result isn't final while that happens.",
    "original_guess": "ai",
    "original_label": "This writing has a lot in common with te…",
    "status": "under_review",
    "timestamp": "2026-11-09T05:46:18+00:00"
  },
  "log_after": [
    {
      "combined_score": 0.9363,
      "content_id": "4ae10887-e404-49ff-b17e-59fa83f411d5",
      "creator_id": "eval_appeal_t1_1",
      "guess": "ai",
      "label": "This writing has a lot in common with te…",
      "model_score": 0.9005,
      "status": "decided",
      "style_score": 0.972,
      "timestamp": "2026-11-09T05:46:18+00:00"
    },
    {
      "combined_score": null,
      "content_id": "4ae10887-e404-49ff-b17e-59fa83f411d5",
      "creator_id": "eval_appeal_t1_1",
      "event": "appeal",
      "guess": null,
      "label": null,
      "model_score": null,
      "reasoning": "Criterion 5 check, trial 1.",
      "status": "under_review",
      "style_score": null,
      "timestamp": "2026-11-09T05:46:18+00:00"
    }
  ],
  "passed": true
}
```

```json
{
  "content_id": "af6054ce-7287-4582-a82b-eae48af8ff23",
  "appeal_status": 404,
  "appeal_response": {
    "error": "unknown_content_id",
    "message": "We couldn't find a result with that content_id. Check it was copied exactly."
  },
  "under_review_entries": 0,
  "passed": true
}
```

*Criterion 1* — no output yet. `scenarios.py` loads every `my_writing/*.txt`
as criterion 1's input and leaves the scenario out until those files exist.

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->

There are no criterion misses to diagnose (criterion 1 has no data). The 20
broken attacks fall into four patterns. Scores are from
`results/audit_extract_before.jsonl`; "avg" is the plain average of the two
signals before the cap.

**1. One signal moving is enough to escape the AI label — 10 breaks.**
EV02, EV03, EV05, EV06, EV07, EV09, EV10, PI01, PI03, PI05.
*Stage: the combining rule and the label mapping.* The combined score is an
equal-weight average and the AI label needs 0.75, so AI text is only caught
when *both* signals stay high; my clearly-AI samples scored 0.83–0.94 because
both did. An attacker only has to pull one signal down to about 0.45. In EV02,
EV06, EV07 and EV10 that signal was signal two — broken-up sentences,
one long sentence beside a short one, punctuation padding and stanza
repetition dropped style to 0.37–0.47, exactly the shape blind spot Milestone 1
named. In EV03 and EV09 (a pasted quotation, a human opening) both signals
sagged to about 0.7; EV05's heavy human edit pulled both under 0.45.
The disagreement cap did nothing here: it fired twice (EV10, MF06) and changed
no label, because both averages were already under 0.75. With a 0.75
threshold, an average with one signal below 0.60 can only reach the AI label
if the other is above 0.90 — so the cap is almost entirely redundant. This is
the trade I chose, fewer accusations for more AI text getting through; the
attack set shows how cheap it is to take the other side of it.

**2. Signal one reads unusual tokens as human — 3 breaks.**
EV01 (typos, model 0.16), PI02 (a fake `SYSTEM:` line, model 0.20), EV08
(10 words, model 0.25).
*Stage: signal one. Mechanism: perplexity rises on anything gpt2 finds
surprising — misspellings, `key=value` syntax, too little context — whatever
wrote the text.* I tested this on PI02: with its injected first line removed,
the same AI paragraph scores model **0.75**, not 0.20. The instruction didn't
work because anything obeyed it — nothing in my service reads instructions —
it worked because its tokens confused signal one, and that moved the label
from "unsure" to "human". EV01 aimed at signal two and signal two held: since I
flipped vocabulary variety, typos make it read *more* AI (style 1.00). Signal
one broke instead.

**3. Both signals share one blind spot — 2 breaks, the false positives.**
FP03 (a careful non-native writer) and FP04 (an essay written to a rubric).
*Stages: signals one and two, and the combining rule.* Plain, regular writing
is predictable to gpt2 (model 0.81, 0.83) and evenly shaped (style 0.72,
0.68). My average treats two signals agreeing as two pieces of evidence, but
here they agree for one reason. Both were above the 0.60 floor, so the cap
couldn't fire, and 0.76 beat the threshold by 0.01. This is the writer my
Milestone 1 trace predicted.

**4. The route accepts text that isn't language — 5 breaks.**
MF03–MF07: control characters, punctuation only, one very long "word", emoji
only, right-to-left script.
*Stage: the route. Mechanism: validation checks type, length and a 3-token
minimum, but never whether the input is prose.* Both signals then produce
meaningless numbers: signal one gives 0.00 or 1.00, and signal two gives
one-"sentence" input a neutral 0.5 spread while vocabulary and punctuation,
with nothing to count, read as fully AI-like. So a single long string is
labelled AI (0.89) and punctuation is labelled human (0.33).

**The pattern across all four:** a single fragile signal decides too much.
Signal one is the easiest to move — it broke three attacks on its own, it
carries most of the false-positive score, and the averaging rule lets any one
signal's drop be enough. The route gap is separate, and the cheapest to close.

---

## The Improvement

**What I changed:** one line — `AI_THRESHOLD` in `config.py`, from **0.75 to
0.80**. Nothing else moved: same weights, floor, cap, signals and route. Every
"after" decision logs `"ai_threshold": 0.8` in its `rule` field, so the two
runs can't be confused in the audit log.

**Which diagnosis pointed at it:** pattern 3 — the shared blind spot. FP03 (a
careful non-native writer) and FP04 (an essay written to a rubric) were real
writing labelled AI at 0.760 and 0.756. Both signals were above the 0.60 floor,
so my disagreement cap couldn't protect them; the only stage left between them
and the accusation was the label mapping. FP03 was my single worst outcome.

I chose this over input validation (pattern 4), which a simulation on the
"before" scores said would cut breaks from 20 to 13 — but leave FP03 standing.
My design has put not accusing real writers first since Milestone 1.

**Caveat:** I picked 0.80 *after* seeing FP03 score 0.76. That is tuning to
the test set. A threshold set this way is only as good as how typical these
two writers are.

### Attack Run — After

`run_attacks.py --set attack_set --label after` — full report with verdicts:
`results/attack_run_2026-11-09_0124_after.md`; the run's log entries:
`results/audit_extract_after.jsonl`. Marked with the same rules as before.

| Family | Rows | Broke before | Broke after |
|---|---|---|---|
| evasion | 10 | 9 | 9 |
| false_positive | 8 | **2** | **0** |
| prompt_injection | 6 | 4 | 4 |
| malformed (both files) | 20 | 5 | 5 |
| flood_same_creator | 12 | 0 | 0 |
| **All** | **56** | **20** | **18** |

The only two rows that changed:

| ID | Combined | Before (AI at 0.75) | After (AI at 0.80) |
|---|---|---|---|
| FP03 non-native writer | 0.760 | **ai** — broke | unsure — held |
| FP04 rubric essay | 0.756 | **ai** — broke | unsure — held |

```json
{"timestamp": "2026-11-09T06:24:55+00:00", "content_id": "526f1c55-859a-4640-9e33-2d3116862450", "creator_id": "attacker_FP03", "guess": "unsure", "model_score": 0.8051, "style_score": 0.7151, "combined_score": 0.7601, "label": "Our automated check couldn't tell whether this was written b…", "status": "decided", "rule": {"weight_model": 0.5, "weight_style": 0.5, "both_signals_floor": 0.6, "disagreement_cap": 0.7, "human_threshold": 0.35, "ai_threshold": 0.8}}
```

```json
{"timestamp": "2026-11-09T06:24:55+00:00", "content_id": "5b1a442e-6652-4a54-bc3b-2e8a0fddfa3d", "creator_id": "attacker_FP04", "guess": "unsure", "model_score": 0.8329, "style_score": 0.6799, "combined_score": 0.7564, "label": "Our automated check couldn't tell whether this was written b…", "status": "decided", "rule": {"weight_model": 0.5, "weight_style": 0.5, "both_signals_floor": 0.6, "disagreement_cap": 0.7, "human_threshold": 0.35, "ai_threshold": 0.8}}
```

### Run Log — After

`run_eval.py --label after` (`results/run_2026-11-09_0126_after.md`) and
`run_checks.py --label after` (`results/checks_2026-11-09_0126_after.json`).

| Criterion | Target | Before (×3) | After: Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|---|
| 1. My own writing is rarely called AI | ≤ 2 of 10 | not run | not run | not run | not run | **no verdict** |
| 2. Clearly-AI and clearly-human far apart | gap ≥ 0.30 | 0.482 | 0.482 | 0.482 | 0.482 | MET |
| 3. Every label is reachable | ≥ 2 per label | 2/2/2 | 2/2/2 | 2/2/2 | 2/2/2 | MET |
| 4. Bad input refused, never labelled | 8 of 8 | 8/8 | 8/8 | 8/8 | 8/8 | MET |
| 5. Every appeal recorded | 7 of 7 | 7/7 | 7/7 | 7/7 | 7/7 | MET |

Criteria 2 and 5 can't move with a threshold — scores don't change, only the
label drawn from them. Criterion 3 still has two AI-labelled inputs because my
two picks score 0.94 and 0.89. Trial 3's JSON-list body again met the limiter
(`429`) rather than validation, as before.

**Did it help, and how do I know:**

It helped the problem I aimed at and nothing else: broken attacks fell from 20
to 18, both false accusations became "unsure", and no other row in the attack
set or the run log changed.

The cost is real but invisible in this set. Every AI text scoring 0.75–0.80
now gets "unsure" instead of "AI". None of the attacks landed there, but
EV04 — the one evasion still caught — scores 0.806, so it now clears the line
by 0.006 instead of 0.056, and my weakest clearly-AI sample (0.83) by 0.03. The
next lightly-edited AI text is more likely to get through, and evasion — 9 of
10 broken — was already my worst family. I made the trade on purpose: a missed
detection costs the site a little, a wrong accusation cost FP03 a lot.

---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->

18 of 56 attacks still get through after the improvement, in the same patterns
the diagnoses named. Each group, what I'd do, and why I stopped.

**AI text landing on "unsure" — EV02, EV03, EV05, EV06, EV07, EV09, EV10,
PI01, PI03, PI05 (pattern 1).** *What I'd do:* add a third signal that doesn't
share the other two's weaknesses — a modern detector model rather than gpt2 —
and stop letting any single signal's drop decide the outcome. Reweighting or
lowering the threshold won't do it: at 0.70 the simulation added FP02 as a new
false accusation. *Why I stopped:* the milestone allows one change, and the
only threshold move that catches more of these accuses more writers. My
improvement made this group slightly easier to join (the AI line is now 0.80).

**Signal one fooled by odd tokens — EV01, PI02, EV08 (pattern 2).** *What I'd
do:* clean the text before signal one reads it — drop lines that look like
instructions or `key=value` syntax, and don't score text too short to give
gpt2 context. On PI02, removing the injected line alone moved the model score
from 0.20 to 0.75. *Why I stopped:* one change; and a cleaning rule good enough
to ship needs its own attack set, because attackers would aim at the cleaner.

**Junk input still labelled — MF03–MF07 (pattern 4).** *What I'd do:* refuse
anything under 40 words before the signals run, with a plain message saying
why. Simulated on the "before" scores it takes breaks from 20 to 13 on its own.
It has two costs I'd have to design around: a short genuine piece (FP08, 8
words) would be refused instead of labelled, and my word counter only counts
Latin letters, so text in other scripts — MF07, right-to-left — would be
refused too. The message would have to say "English prose, at least 40 words",
honestly, rather than pretend those writers sent junk. *Why I stopped:* I spent
my one change on the false accusations instead.

**RQ10 and RQ11 — not really tested.** Both met the rate limiter before my
route, in both runs. *What I'd do:* rerun them alone after the window resets.
*Why I stopped:* nothing got through either way, and the route already returns
`400` for the same kind of body when it reaches it.

**The rate limit can be dodged.** Not an attack in the set, but the limit
counts per `creator_id`, so a script that sends a new one each time is never
limited. *What I'd do:* add a per-IP ceiling alongside the per-creator one.
*Why I stopped:* out of scope for one change, and a per-IP limit punishes
shared networks — a school or a household — which needs its own numbers.

**Criterion 1 — no verdict.** *What I'd do:* collect ten pieces of my own
writing into `my_writing/` and run it; `scenarios.py` already loads them.
*Why I stopped:* I haven't collected those pieces yet, so the criterion that
matters most to a real writer is the one I can't call.

**Criterion 3 — met, but too easy.** I chose its inputs after seeing their
scores. *What I'd do:* fix the inputs before scoring and require a share of a
natural set to land in each band.

**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->

I'd keep erring toward fewer wrong accusations — the 0.80 threshold and a wide
"unsure" band — because a false "AI" label lands on one person who can do
little about it, often a plain or non-native writer like FP03. The cost is paid
by the site and its readers, who will see more AI text pass as "unsure", and by
honest writers whose work now competes with AI-written pieces that got through.

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
