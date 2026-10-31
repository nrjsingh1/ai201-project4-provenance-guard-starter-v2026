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
| high-confidence human |  |  |
| unsure |  |  |
| high-confidence AI |  |  |

**Why I worded the "unsure" one this way:**
<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->



---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

<!-- Milestone 3 run: one signal only. guess, label and confidence are
     placeholders until Milestones 4 and 5. -->

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "Artificial intelligence is transforming the way we live and work. It offers numerous benefits, including increased efficiency, improved decision-making, and enhanced productivity. However, it is important to consider the potential challenges and ethical implications.", "creator_id": "neeraj"}'
```

```json
{
  "combined_score": null,
  "confidence": 0.0,
  "content_id": "e23b31c8-b35f-4365-973c-a80a49452ddb",
  "creator_id": "neeraj",
  "guess": null,
  "label": "PLACEHOLDER — labels arrive in Milestone 5.",
  "model_score": 0.8785,
  "status": "decided",
  "style_score": null,
  "timestamp": "2026-10-29T01:44:12+00:00"
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

**The log after those requests**

```bash
$ curl "http://127.0.0.1:5000/log?limit=3"
```

```json
{
  "count": 3,
  "entries": [
    {"creator_id": "x", "event": "rejected", "http_status": 413, "reason": "text_too_long", "status": "rejected", "text_length": 20001, "timestamp": "2026-10-29T01:44:13+00:00"},
    {"creator_id": "unknown", "event": "rejected", "http_status": 400, "reason": "invalid_json", "status": "rejected", "timestamp": "2026-10-29T01:44:13+00:00"},
    {"combined_score": null, "content_id": "e90aa17b-084f-4010-ac32-8317a5536049", "creator_id": "neeraj", "guess": null, "label": "PLACEHOLDER — labels arrive in Milestone 5.", "model_score": 0.316, "status": "decided", "style_score": null, "timestamp": "2026-10-29T01:44:18+00:00"}
  ]
}
```

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "...", "reasoning": "..."}'
```

```json

```

**What the log shows afterwards**

```bash
$ curl "http://127.0.0.1:5000/log?limit=3"
```

```json

```

---

## How I Used AI

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

```

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



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



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
