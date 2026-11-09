"""
What your test runs. ← UNIT 8, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
false positives needs your own writing. One about label coverage needs inputs
across the score range. One about the appeal path needs a real content_id.

Working that out is Milestone 3's first step, and this file is where you write
it down. `run_eval.py` runs everything here three times.

Two are filled in as examples. Replace them with what your criteria actually
need — these are a shape, not a set.

A scenario carries **either** of these:

    "texts"   a list of strings. Each is sent as {"text": ..., "creator_id": ...}
              with a creator_id made up for you. Use this for most criteria.

    "bodies"  a list of whole request bodies, sent exactly as written. Use this
              when the malformed request IS the point — empty text, no `text`
              field at all, something enormous. A bad-input criterion needs it,
              because you cannot express "the field is missing" as a string.
"""

from pathlib import Path

import eval_texts

# Criterion 1 is MY writing, one piece per .txt file in my_writing/. Nothing
# else counts, so until those files exist the scenario is left out rather than
# filled with someone else's prose.
MY_WRITING = sorted(Path(__file__).parent.glob("my_writing/*.txt"))

SCENARIOS = [
    *([{
        "name": "my own writing",
        "criterion": 1,
        "texts": [p.read_text(encoding="utf-8").strip() for p in MY_WRITING],
    }] if MY_WRITING else []),
    {
        "name": "clearly AI",
        "criterion": 2,
        "texts": eval_texts.CLEARLY_AI,
    },
    {
        "name": "clearly human",
        "criterion": 2,
        "texts": eval_texts.CLEARLY_HUMAN,
    },
    {
        "name": "label coverage",
        "criterion": 3,
        # Two inputs aimed at each label, picked from texts whose scores I'd
        # already seen: human, human, unsure, unsure, AI, AI.
        "texts": [
            eval_texts.CLEARLY_HUMAN[0],     # Twain
            eval_texts.CLEARLY_HUMAN[1],     # Melville
            eval_texts.CLEARLY_HUMAN[4],     # Darwin
            eval_texts.LIGHTLY_EDITED_AI,
            eval_texts.CLEARLY_AI[0],
            eval_texts.CLEARLY_AI[1],
        ],
    },
    {
        "name": "bad input",
        "criterion": 4,
        # Seven of criterion 4's eight. The eighth — a body that is a JSON list
        # — can't be a dict, so run_checks.py sends it.
        "bodies": [
            {"creator_id": "eval_bad_missing"},
            {"text": "", "creator_id": "eval_bad_empty"},
            {"text": "   \n\t  ", "creator_id": "eval_bad_whitespace"},
            {"text": None, "creator_id": "eval_bad_null"},
            {"text": 42, "creator_id": "eval_bad_number"},
            {"text": "word " * 5000, "creator_id": "eval_bad_huge"},
            {"text": eval_texts.CLEARLY_AI[2]},           # no creator_id
        ],
    },
    # Criterion 5 (appeals) needs a submission and then an appeal against the
    # content_id that came back, which run_eval.py can't do. run_checks.py does.
]


def validate() -> list[str]:
    """
    Complain about anything malformed, before a long run rather than during.

    A "bodies" scenario is deliberately exempt from the empty check — an empty
    string is the whole point of a bad-input case, and refusing to run one
    would make that criterion untestable.
    """
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("name"):
            problems.append(f"scenario {i} has no name")

        texts = scenario.get("texts")
        bodies = scenario.get("bodies")

        if texts and bodies:
            problems.append(
                f"scenario {i} ('{scenario.get('name')}') has both texts and "
                f"bodies — pick one"
            )
            continue

        if bodies:
            for j, body in enumerate(bodies, 1):
                if not isinstance(body, dict):
                    problems.append(
                        f"scenario {i}, body {j} is not a dict — bodies are whole "
                        f"request bodies, like {{'text': '', 'creator_id': 'x'}}"
                    )
            continue

        if not texts:
            problems.append(f"scenario {i} has no texts and no bodies")
            continue

        for j, text in enumerate(texts, 1):
            if not str(text).strip():
                problems.append(
                    f"scenario {i}, text {j} is empty — if an empty submission is what "
                    f"you're testing, use 'bodies' instead of 'texts'"
                )
            elif str(text).startswith("REPLACE ME"):
                problems.append(
                    f"scenario {i} ('{scenario.get('name')}'), text {j} is still "
                    f"the placeholder"
                )
    return problems
