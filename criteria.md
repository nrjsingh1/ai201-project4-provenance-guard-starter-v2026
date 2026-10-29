# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---
## 1. My own writing is rarely called AI

Of 10 pieces I wrote myself (150–400 words each, at least 4 of them written
plainly — short sentences, everyday vocabulary), **at most 2 are labelled
high-confidence AI, in each of the three trials.**

**Why this target:** A wrong accusation is the expensive mistake, and my
Milestone 1 trace showed that plain human writing looks AI-like to *both*
signals, so it's the case I most need to measure. I chose 2 rather than 0
because zero would mean an unsure band so wide that the AI label is almost
unreachable, which would break criterion 3. I read the message a writer caught
by this rate might send me and kept the number, so it has to be met in all
three trials, not on average.

---

## 2. Clearly-AI and clearly-human text land far apart

Across 5 clearly-AI samples (unedited model output) and 5 clearly-human
samples, **the mean combined score of the AI samples is at least 0.30 higher
than the mean combined score of the human samples, in each of the three
trials.**

**Why this target:** If the easy cases don't separate, the hard ones never
will, and the thresholds have no room to sit in. 0.30 is the width of the
placeholder unsure band (0.35–0.65); a smaller gap would mean the two groups
could both fall inside "unsure" and the system would be telling nobody
anything.

---

## 3. Every label is actually reachable

**Each of the three labels — high-confidence human, unsure, high-confidence
AI — is produced by at least 2 different inputs, in each of the three
trials.**

**Why this target:** A label nothing can reach is a gap in my ranges. And
with gpt2 scoring the same text slightly differently on repeat runs, a label
that only one lucky input reaches might vanish on the next trial. Two inputs
per label shows the range genuinely covers it.

---

## 4. Bad input is refused, never labelled

These 8 requests to `POST /submit` — `text` missing, `text` empty (`""`),
`text` whitespace only, `text` `null`, `text` a number, `text` over 20,000
characters, `creator_id` missing, and a body that is a JSON list instead of an
object — **each return a 4xx status with an `error` field and no `guess` or
`label` field: 8 of 8, zero 500s, in each of the three trials.**

**Why this target:** A crash on malformed input is one of the most common real
failures, and an attacker will send exactly these. Worse than crashing would be
*labelling* something that couldn't be scored: an empty submission called
"human" or "AI" is a decision about nothing. Every one must be refused, so
the target is all 8.

---

## 5. Every appeal is recorded and changes status

For 5 appeals sent to `POST /appeal` with real `content_id`s from earlier
submissions, **all 5 return 200, and for each one `GET /log` shows a new entry
with `status: "under_review"` while the original `decided` entry is still
there unchanged.** Two appeals with made-up `content_id`s **both return 404
and add no `under_review` entry.** Checked by hand with `curl`, since
`run_eval.py` only calls `/submit`.

**Why this target:** The appeal is the only thing between a wrong accusation
and nothing at all, so "usually works" isn't good enough: 5 of 5. The 404 half
matters too — a typo'd id that silently "succeeds" tells a writer their appeal
is in when it isn't, which is worse than an error.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
