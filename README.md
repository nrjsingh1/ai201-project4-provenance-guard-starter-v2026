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
| high-confidence human | 0.00 – 0.35 | This reads like it was written by a person. Our automated check found nothing in the writing that suggests it was generated by AI. |
| unsure | 0.35 – 0.75 | Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review. |
| high-confidence AI | 0.75 – 1.00 | This writing has a lot in common with text generated by AI. That's what our automated check found in its patterns. It isn't proof of how it was written, and the check can be wrong, especially about simple or plain writing. If you wrote this yourself, you can ask for a person to review it. |

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
