# Attack run — before

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 56 attacks · 2026-11-09 00:35
- Auto-marked BROKE (5xx, crash, no response): **0**
- Left for you to judge: **56**

The Verdict column is blank where a script can't honestly decide. Whether
an evasion worked depends on where you put your thresholds — read the
`targets` column, look at what came back, and write HELD or BROKE yourself.

Each attack submits as creator_id `attacker_<id>`, and the content_id it
came back with is in the table — either one will match this run against your
audit log when you go looking for the ten entries to paste.

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | `057ce557-d8cc-405f-8d12-0d352fad3043` | unsure | 0.163 | BROKE |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `d148750f-5e6e-48d1-bd78-f45f0f2a44ce` | unsure | 0.032 | BROKE |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `ef3a6057-d1f2-428e-844f-f5a7fb670258` | unsure | 0.329 | BROKE |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `4593011a-63e6-42a6-ae33-fdd58e578406` | ai | 0.611 | HELD |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `21e90a73-195a-4a06-9a92-27336d6ef68d` | unsure | 0.269 | BROKE |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `d011a578-5ba0-44a0-90ec-f6f5aab3ff67` | unsure | 0.023 | BROKE |
| EV07 | evasion | signal two: padding with punctuation | 200 | `1d45b3e7-6285-4661-a224-36e21068768b` | unsure | 0.055 | BROKE |
| EV08 | evasion | signal one: text below the token window | 200 | `7c44f997-bcf2-436e-bf32-0f6912cf8e86` | unsure | 0.020 | BROKE |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `5836bcd9-7302-4069-a590-491f384e8f18` | unsure | 0.437 | BROKE |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `e8228515-5043-4802-8ab7-7356cddb498b` | unsure | 0.400 | BROKE |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `1b2c758a-e412-40bd-8fb4-f5309217dd0c` | unsure | 0.178 | HELD |
| FP02 | false_positive | human writing in a formal register | 200 | `690630ff-7b6b-44eb-9081-cbf5e4340df2` | unsure | 0.445 | HELD |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `b30ade61-c70a-4d52-be03-79af9629fa2f` | ai | 0.520 | BROKE |
| FP04 | false_positive | a student essay written to a rubric | 200 | `c252f404-a960-43af-9b96-67b68b1b667d` | ai | 0.513 | BROKE |
| FP05 | false_positive | technical documentation written by a person | 200 | `d3669991-26e0-4554-ad07-dcf020958d6c` | unsure | 0.374 | HELD |
| FP06 | false_positive | a person imitating a formal template | 200 | `80b420e6-5997-4203-bf9b-2718a40b5e19` | unsure | 0.282 | HELD |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `bedd10e2-0800-4a7c-997a-ac56f6f06456` | unsure | 0.082 | HELD |
| FP08 | false_positive | very short genuine human submission | 200 | `a85ef551-d6b6-4a0a-a21a-03c999b639ba` | unsure | 0.089 | HELD |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `ef54d4a3-fd4f-46e4-9c26-7608ccb2d40f` | unsure | 0.013 | BROKE |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `f1ad0261-dd14-43b4-acb1-dacf62f133ec` | human | 0.357 | BROKE |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `e0498906-d9fb-4ecc-843b-e71fa9a3e6ed` | unsure | 0.251 | BROKE |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `f029c7a0-748e-4797-9e1c-cc01b40e0043` | unsure | 0.029 | HELD |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `f0580668-d8fc-4330-9b69-591da6037a61` | unsure | 0.215 | BROKE |
| PI06 | prompt_injection | instruction plus real human text | 200 | `b7de9eb5-4b13-42bd-8935-56b6ba398427` | unsure | 0.143 | HELD |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — | HELD |
| MF02 | malformed | text is a single character | 422 | `—` | — | — | HELD |
| MF03 | malformed | text is control characters | 200 | `f1390c1c-eece-491b-a730-56070a2cf2a0` | unsure | 0.225 | BROKE |
| MF04 | malformed | text is only punctuation | 200 | `33b01a34-b379-4141-93e8-09139cffeeb9` | human | 0.339 | BROKE |
| MF05 | malformed | text is a very long single word | 200 | `717194b9-68f3-4af6-9e88-bf1bfda0a13b` | ai | 0.773 | BROKE |
| MF06 | malformed | text is emoji only | 200 | `4a02f07f-5690-4d3b-a3c8-76da4a1d035a` | unsure | 0.400 | BROKE |
| MF07 | malformed | text is right-to-left script | 200 | `ae1ddd31-e70a-4b23-b7c2-4aae09c2846e` | unsure | 0.331 | BROKE |
| MF08 | malformed | text is 60,000 characters | 413 | `—` | — | — | HELD |
| RQ01 | malformed | no text field at all | 400 | `—` | — | — | HELD |
| RQ02 | malformed | no creator_id | 400 | `—` | — | — | HELD |
| RQ03 | malformed | text is a number | 400 | `—` | — | — | HELD |
| RQ04 | malformed | text is a list | 400 | `—` | — | — | HELD |
| RQ05 | malformed | text is null | 400 | `—` | — | — | HELD |
| RQ06 | malformed | creator_id is an object | 400 | `—` | — | — | HELD |
| RQ07 | malformed | body is a JSON array, not an object | 400 | `—` | — | — | HELD |
| RQ08 | malformed | body is unparseable JSON | 400 | `—` | — | — | HELD |
| RQ09 | malformed | body is empty | 400 | `—` | — | — | HELD |
| RQ10 | malformed | body is form-encoded, not JSON | 429 | `—` | — | — | HELD |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | `—` | — | — | HELD |
| RQ12 | malformed | deeply nested JSON | 400 | `—` | — | — | HELD |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | `5843dd69-4f33-48ca-b573-4890be350d62` | unsure | 0.196 | HELD |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | `d0dc19c3-e60d-49fb-b56c-be1a08fbade5` | unsure | 0.196 | HELD |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | `4fe568fe-1a48-4561-9361-676cba9303d7` | unsure | 0.196 | HELD |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | `1f6546e6-5a10-4727-a47b-ffa03522b049` | unsure | 0.196 | HELD |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | `ab822be5-189c-42a8-bf57-d963e8131c0e` | unsure | 0.196 | HELD |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |

---

## By family

| Family | Attacks | Auto-BROKE | Left to judge |
|---|---|---|---|
| `evasion` | 10 | 0 | 10 |
| `false_positive` | 8 | 0 | 8 |
| `flood_same_creator` | 12 | 0 | 12 |
| `malformed` | 20 | 0 | 20 |
| `prompt_injection` | 6 | 0 | 6 |

> The **false_positive** family is the one to look at hardest. Those are
> written to be genuine human writing that reads as machine-like. Every one
> your service calls AI is a real writer it would have accused.

---

## What came back

The detail behind the table. Paste the interesting failures into your
README — the ones that show something, not the ten easiest.

### EV01 — `evasion`

*Targeting:* signal two: typos raise word variety

```json
{
  "id": "EV01",
  "status": 200,
  "content_id": "057ce557-d8cc-405f-8d12-0d352fad3043",
  "creator_id": "attacker_EV01",
  "guess": "unsure",
  "confidence": 0.1634,
  "model_score": 0.1635,
  "style_score": 1.0,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV02 — `evasion`

*Targeting:* signal two: broken-up sentences raise length spread

```json
{
  "id": "EV02",
  "status": 200,
  "content_id": "d148750f-5e6e-48d1-bd78-f45f0f2a44ce",
  "creator_id": "attacker_EV02",
  "guess": "unsure",
  "confidence": 0.0316,
  "model_score": 0.5943,
  "style_score": 0.3741,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV03 — `evasion`

*Targeting:* signal two: a pasted quotation changes the shape

```json
{
  "id": "EV03",
  "status": 200,
  "content_id": "ef3a6057-d1f2-428e-844f-f5a7fb670258",
  "creator_id": "attacker_EV03",
  "guess": "unsure",
  "confidence": 0.3286,
  "model_score": 0.6662,
  "style_score": 0.6623,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV04 — `evasion`

*Targeting:* signal one: unusual words raise perplexity

```json
{
  "id": "EV04",
  "status": 200,
  "content_id": "4593011a-63e6-42a6-ae33-fdd58e578406",
  "creator_id": "attacker_EV04",
  "guess": "ai",
  "confidence": 0.6114,
  "model_score": 0.6114,
  "style_score": 1.0,
  "label": "This writing has a lot in common with text generated by AI. That's what our automated check found in its patterns. It isn't proof of how it was written, and the check can be wrong, especially about simple or plain writing. If you wrote this yourself, you can ask for a person to review it.",
  "error": null,
  "verdict": ""
}
```

### EV05 — `evasion`

*Targeting:* both signals: heavy human editing pass

```json
{
  "id": "EV05",
  "status": 200,
  "content_id": "21e90a73-195a-4a06-9a92-27336d6ef68d",
  "creator_id": "attacker_EV05",
  "guess": "unsure",
  "confidence": 0.2686,
  "model_score": 0.3212,
  "style_score": 0.4101,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV06 — `evasion`

*Targeting:* signal two: one very long sentence and one very short

```json
{
  "id": "EV06",
  "status": 200,
  "content_id": "d011a578-5ba0-44a0-90ec-f6f5aab3ff67",
  "creator_id": "attacker_EV06",
  "guess": "unsure",
  "confidence": 0.0232,
  "model_score": 0.5727,
  "style_score": 0.4505,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV07 — `evasion`

*Targeting:* signal two: padding with punctuation

```json
{
  "id": "EV07",
  "status": 200,
  "content_id": "1d45b3e7-6285-4661-a224-36e21068768b",
  "creator_id": "attacker_EV07",
  "guess": "unsure",
  "confidence": 0.055,
  "model_score": 0.5862,
  "style_score": 0.4688,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV08 — `evasion`

*Targeting:* signal one: text below the token window

```json
{
  "id": "EV08",
  "status": 200,
  "content_id": "7c44f997-bcf2-436e-bf32-0f6912cf8e86",
  "creator_id": "attacker_EV08",
  "guess": "unsure",
  "confidence": 0.0202,
  "model_score": 0.2452,
  "style_score": 0.775,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV09 — `evasion`

*Targeting:* both: AI text with a human opening paragraph bolted on

```json
{
  "id": "EV09",
  "status": 200,
  "content_id": "5836bcd9-7302-4069-a590-491f384e8f18",
  "creator_id": "attacker_EV09",
  "guess": "unsure",
  "confidence": 0.4368,
  "model_score": 0.7042,
  "style_score": 0.7325,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV10 — `evasion`

*Targeting:* signal two: repeated stanza structure

```json
{
  "id": "EV10",
  "status": 200,
  "content_id": "e8228515-5043-4802-8ab7-7356cddb498b",
  "creator_id": "attacker_EV10",
  "guess": "unsure",
  "confidence": 0.4,
  "model_score": 0.9792,
  "style_score": 0.4561,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP01 — `false_positive`

*Targeting:* plain, clear human writing with no flourishes

```json
{
  "id": "FP01",
  "status": 200,
  "content_id": "1b2c758a-e412-40bd-8fb4-f5309217dd0c",
  "creator_id": "attacker_FP01",
  "guess": "unsure",
  "confidence": 0.1778,
  "model_score": 0.6175,
  "style_score": 0.5603,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP02 — `false_positive`

*Targeting:* human writing in a formal register

```json
{
  "id": "FP02",
  "status": 200,
  "content_id": "690630ff-7b6b-44eb-9081-cbf5e4340df2",
  "creator_id": "attacker_FP02",
  "guess": "unsure",
  "confidence": 0.4448,
  "model_score": 0.7387,
  "style_score": 0.7061,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP03 — `false_positive`

*Targeting:* a non-native English speaker writing carefully

```json
{
  "id": "FP03",
  "status": 200,
  "content_id": "b30ade61-c70a-4d52-be03-79af9629fa2f",
  "creator_id": "attacker_FP03",
  "guess": "ai",
  "confidence": 0.5202,
  "model_score": 0.8051,
  "style_score": 0.7151,
  "label": "This writing has a lot in common with text generated by AI. That's what our automated check found in its patterns. It isn't proof of how it was written, and the check can be wrong, especially about simple or plain writing. If you wrote this yourself, you can ask for a person to review it.",
  "error": null,
  "verdict": ""
}
```

### FP04 — `false_positive`

*Targeting:* a student essay written to a rubric

```json
{
  "id": "FP04",
  "status": 200,
  "content_id": "c252f404-a960-43af-9b96-67b68b1b667d",
  "creator_id": "attacker_FP04",
  "guess": "ai",
  "confidence": 0.5128,
  "model_score": 0.8329,
  "style_score": 0.6799,
  "label": "This writing has a lot in common with text generated by AI. That's what our automated check found in its patterns. It isn't proof of how it was written, and the check can be wrong, especially about simple or plain writing. If you wrote this yourself, you can ask for a person to review it.",
  "error": null,
  "verdict": ""
}
```

### FP05 — `false_positive`

*Targeting:* technical documentation written by a person

```json
{
  "id": "FP05",
  "status": 200,
  "content_id": "d3669991-26e0-4554-ad07-dcf020958d6c",
  "creator_id": "attacker_FP05",
  "guess": "unsure",
  "confidence": 0.3736,
  "model_score": 0.8005,
  "style_score": 0.5731,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP06 — `false_positive`

*Targeting:* a person imitating a formal template

```json
{
  "id": "FP06",
  "status": 200,
  "content_id": "80b420e6-5997-4203-bf9b-2718a40b5e19",
  "creator_id": "attacker_FP06",
  "guess": "unsure",
  "confidence": 0.2822,
  "model_score": 0.8814,
  "style_score": 0.4008,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP07 — `false_positive`

*Targeting:* human writing that repeats a phrase deliberately

```json
{
  "id": "FP07",
  "status": 200,
  "content_id": "bedd10e2-0800-4a7c-997a-ac56f6f06456",
  "creator_id": "attacker_FP07",
  "guess": "unsure",
  "confidence": 0.0816,
  "model_score": 0.8816,
  "style_score": 0.2,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP08 — `false_positive`

*Targeting:* very short genuine human submission

```json
{
  "id": "FP08",
  "status": 200,
  "content_id": "a85ef551-d6b6-4a0a-a21a-03c999b639ba",
  "creator_id": "attacker_FP08",
  "guess": "unsure",
  "confidence": 0.0892,
  "model_score": 0.3223,
  "style_score": 0.767,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### PI01 — `prompt_injection`

*Targeting:* instruction to ignore the check

```json
{
  "id": "PI01",
  "status": 200,
  "content_id": "ef54d4a3-fd4f-46e4-9c26-7608ccb2d40f",
  "creator_id": "attacker_PI01",
  "guess": "unsure",
  "confidence": 0.0126,
  "model_score": 0.4625,
  "style_score": 0.55,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### PI02 — `prompt_injection`

*Targeting:* instruction disguised as a system message

```json
{
  "id": "PI02",
  "status": 200,
  "content_id": "f1ad0261-dd14-43b4-acb1-dacf62f133ec",
  "creator_id": "attacker_PI02",
  "guess": "human",
  "confidence": 0.3568,
  "model_score": 0.2044,
  "style_score": 0.4389,
  "label": "This reads like it was written by a person. Our automated check found nothing in the writing that suggests it was generated by AI.",
  "error": null,
  "verdict": ""
}
```

### PI03 — `prompt_injection`

*Targeting:* instruction wrapped in the writer's voice

```json
{
  "id": "PI03",
  "status": 200,
  "content_id": "e0498906-d9fb-4ecc-843b-e71fa9a3e6ed",
  "creator_id": "attacker_PI03",
  "guess": "unsure",
  "confidence": 0.2512,
  "model_score": 0.5943,
  "style_score": 0.6569,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### PI04 — `prompt_injection`

*Targeting:* attempt to make the label text hostile

```json
{
  "id": "PI04",
  "status": 200,
  "content_id": "f029c7a0-748e-4797-9e1c-cc01b40e0043",
  "creator_id": "attacker_PI04",
  "guess": "unsure",
  "confidence": 0.0294,
  "model_score": 0.4998,
  "style_score": 0.5295,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### PI05 — `prompt_injection`

*Targeting:* attempt to inject into the audit log

```json
{
  "id": "PI05",
  "status": 200,
  "content_id": "f0580668-d8fc-4330-9b69-591da6037a61",
  "creator_id": "attacker_PI05",
  "guess": "unsure",
  "confidence": 0.2152,
  "model_score": 0.6401,
  "style_score": 0.575,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### PI06 — `prompt_injection`

*Targeting:* instruction plus real human text

```json
{
  "id": "PI06",
  "status": 200,
  "content_id": "b7de9eb5-4b13-42bd-8935-56b6ba398427",
  "creator_id": "attacker_PI06",
  "guess": "unsure",
  "confidence": 0.1428,
  "model_score": 0.5583,
  "style_score": 0.5845,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### MF01 — `malformed`

*Targeting:* text is only whitespace

```json
{
  "id": "MF01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF02 — `malformed`

*Targeting:* text is a single character

```json
{
  "id": "MF02",
  "status": 422,
  "content_id": null,
  "creator_id": "attacker_MF02",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF03 — `malformed`

*Targeting:* text is control characters

```json
{
  "id": "MF03",
  "status": 200,
  "content_id": "f1390c1c-eece-491b-a730-56070a2cf2a0",
  "creator_id": "attacker_MF03",
  "guess": "unsure",
  "confidence": 0.225,
  "model_score": 0.0,
  "style_score": 0.775,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### MF04 — `malformed`

*Targeting:* text is only punctuation

```json
{
  "id": "MF04",
  "status": 200,
  "content_id": "33b01a34-b379-4141-93e8-09139cffeeb9",
  "creator_id": "attacker_MF04",
  "guess": "human",
  "confidence": 0.3388,
  "model_score": 0.0112,
  "style_score": 0.65,
  "label": "This reads like it was written by a person. Our automated check found nothing in the writing that suggests it was generated by AI.",
  "error": null,
  "verdict": ""
}
```

### MF05 — `malformed`

*Targeting:* text is a very long single word

```json
{
  "id": "MF05",
  "status": 200,
  "content_id": "717194b9-68f3-4af6-9e88-bf1bfda0a13b",
  "creator_id": "attacker_MF05",
  "guess": "ai",
  "confidence": 0.7726,
  "model_score": 0.9976,
  "style_score": 0.775,
  "label": "This writing has a lot in common with text generated by AI. That's what our automated check found in its patterns. It isn't proof of how it was written, and the check can be wrong, especially about simple or plain writing. If you wrote this yourself, you can ask for a person to review it.",
  "error": null,
  "verdict": ""
}
```

### MF06 — `malformed`

*Targeting:* text is emoji only

```json
{
  "id": "MF06",
  "status": 200,
  "content_id": "4a02f07f-5690-4d3b-a3c8-76da4a1d035a",
  "creator_id": "attacker_MF06",
  "guess": "unsure",
  "confidence": 0.4,
  "model_score": 0.9969,
  "style_score": 0.425,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### MF07 — `malformed`

*Targeting:* text is right-to-left script

```json
{
  "id": "MF07",
  "status": 200,
  "content_id": "ae1ddd31-e70a-4b23-b7c2-4aae09c2846e",
  "creator_id": "attacker_MF07",
  "guess": "unsure",
  "confidence": 0.3314,
  "model_score": 0.9064,
  "style_score": 0.425,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### MF08 — `malformed`

*Targeting:* text is 60,000 characters

```json
{
  "id": "MF08",
  "status": 413,
  "content_id": null,
  "creator_id": "attacker_MF08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ01 — `malformed`

*Targeting:* no text field at all

```json
{
  "id": "RQ01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ02 — `malformed`

*Targeting:* no creator_id

```json
{
  "id": "RQ02",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ03 — `malformed`

*Targeting:* text is a number

```json
{
  "id": "RQ03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ04 — `malformed`

*Targeting:* text is a list

```json
{
  "id": "RQ04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ05 — `malformed`

*Targeting:* text is null

```json
{
  "id": "RQ05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ06 — `malformed`

*Targeting:* creator_id is an object

```json
{
  "id": "RQ06",
  "status": 400,
  "content_id": null,
  "creator_id": {
    "id": "x"
  },
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ07 — `malformed`

*Targeting:* body is a JSON array, not an object

```json
{
  "id": "RQ07",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ08 — `malformed`

*Targeting:* body is unparseable JSON

```json
{
  "id": "RQ08",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ09 — `malformed`

*Targeting:* body is empty

```json
{
  "id": "RQ09",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ10 — `malformed`

*Targeting:* body is form-encoded, not JSON

```json
{
  "id": "RQ10",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ11 — `malformed`

*Targeting:* body is JSON claiming to be plain text

```json
{
  "id": "RQ11",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ12 — `malformed`

*Targeting:* deeply nested JSON

```json
{
  "id": "RQ12",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ12",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_01 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_01",
  "status": 200,
  "content_id": "5843dd69-4f33-48ca-b573-4890be350d62",
  "creator_id": "attacker_flood",
  "guess": "unsure",
  "confidence": 0.1964,
  "model_score": 0.0287,
  "style_score": 0.775,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FL01_02 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_02",
  "status": 200,
  "content_id": "d0dc19c3-e60d-49fb-b56c-be1a08fbade5",
  "creator_id": "attacker_flood",
  "guess": "unsure",
  "confidence": 0.1964,
  "model_score": 0.0287,
  "style_score": 0.775,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FL01_03 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_03",
  "status": 200,
  "content_id": "4fe568fe-1a48-4561-9361-676cba9303d7",
  "creator_id": "attacker_flood",
  "guess": "unsure",
  "confidence": 0.1964,
  "model_score": 0.0287,
  "style_score": 0.775,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FL01_04 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_04",
  "status": 200,
  "content_id": "1f6546e6-5a10-4727-a47b-ffa03522b049",
  "creator_id": "attacker_flood",
  "guess": "unsure",
  "confidence": 0.1964,
  "model_score": 0.0287,
  "style_score": 0.775,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FL01_05 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_05",
  "status": 200,
  "content_id": "ab822be5-189c-42a8-bf57-d963e8131c0e",
  "creator_id": "attacker_flood",
  "guess": "unsure",
  "confidence": 0.1964,
  "model_score": 0.0287,
  "style_score": 0.775,
  "label": "Our automated check couldn't tell whether this was written by a person or generated by AI. That isn't a finding against the writer: a lot of people's own writing lands here, especially plain, clear writing. Nothing more happens because of this result. If you'd like a person to look at it anyway, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FL01_06 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_06",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_07 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_07",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_08 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_08",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_09 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_09",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_10 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_10",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_11 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_11",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_12 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_12",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```
