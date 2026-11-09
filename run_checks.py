#!/usr/bin/env python3
"""
The checks run_eval.py can't make. Three trials, like run_eval.py.

    python app.py                              # in one terminal
    python run_checks.py --label before        # in another

Criterion 5 — every appeal is recorded and changes status. Each trial submits
5 texts, appeals each content_id, and reads GET /log back: the appeal must
return 200, add an under_review entry, and leave the original decided entry
exactly as it was. Then 2 made-up content_ids must return 404 and add nothing.

Criterion 4, eighth request — a body that is a JSON list. run_eval.py only
sends dicts, so it can't express this one.

Writes results/checks_<date>_<label>.json with every response.
"""

import argparse
import datetime as dt
import json
import uuid

import config
import eval_texts

DEFAULT_URL = f"http://{config.HOST}:{config.PORT}"


def log_for(requests, url, content_id):
    entries = requests.get(f"{url}/log", timeout=30).json()["entries"]
    return [e for e in entries if e.get("content_id") == content_id]


def appeal_trial(requests, url, trial):
    """Criterion 5, one trial. Returns (passed, total, evidence)."""
    evidence = []
    passed = 0
    texts = eval_texts.CLEARLY_AI[:3] + eval_texts.CLEARLY_HUMAN[:2]

    for i, text in enumerate(texts, 1):
        sub = requests.post(f"{url}/submit", timeout=90, json={
            "text": text, "creator_id": f"eval_appeal_t{trial}_{i}"}).json()
        cid = sub["content_id"]
        before = [e for e in log_for(requests, url, cid) if e["status"] == "decided"]

        resp = requests.post(f"{url}/appeal", timeout=30, json={
            "content_id": cid, "reasoning": f"Criterion 5 check, trial {trial}."})
        after = log_for(requests, url, cid)
        decided_after = [e for e in after if e["status"] == "decided"]
        reviews = [e for e in after if e["status"] == "under_review"]

        ok = (resp.status_code == 200 and len(reviews) == 1
              and len(before) == 1 and decided_after == before)
        passed += ok
        evidence.append({"content_id": cid, "appeal_status": resp.status_code,
                         "appeal_response": resp.json(), "log_after": after,
                         "passed": ok})

    for _ in range(2):
        fake = str(uuid.uuid4())
        resp = requests.post(f"{url}/appeal", timeout=30, json={
            "content_id": fake, "reasoning": "This id was never issued."})
        reviews = [e for e in log_for(requests, url, fake)
                   if e["status"] == "under_review"]
        ok = resp.status_code == 404 and not reviews
        passed += ok
        evidence.append({"content_id": fake, "appeal_status": resp.status_code,
                         "appeal_response": resp.json(),
                         "under_review_entries": len(reviews), "passed": ok})

    return passed, len(evidence), evidence


def list_body_trial(requests, url):
    """Criterion 4's eighth request: 4xx, an error field, no guess or label."""
    resp = requests.post(f"{url}/submit", timeout=30, data='["not", "an", "object"]',
                         headers={"Content-Type": "application/json"})
    payload = resp.json()
    ok = (400 <= resp.status_code < 500 and "error" in payload
          and "guess" not in payload and "label" not in payload)
    return ok, {"status": resp.status_code, "response": payload, "passed": ok}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--label", default="")
    parser.add_argument("--url", default=DEFAULT_URL)
    args = parser.parse_args()

    import requests

    report = {"label": args.label, "trials": []}
    for trial in range(1, args.trials + 1):
        passed, total, evidence = appeal_trial(requests, args.url, trial)
        list_ok, list_evidence = list_body_trial(requests, args.url)
        print(f"trial {trial}: criterion 5 {passed}/{total}   "
              f"criterion 4 list body {'refused' if list_ok else 'NOT refused'} "
              f"({list_evidence['status']})")
        report["trials"].append({
            "criterion_5": {"passed": passed, "total": total, "evidence": evidence},
            "criterion_4_list_body": list_evidence,
        })

    config.RESULTS_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    path = config.RESULTS_DIR / f"checks_{stamp}{'_' + args.label if args.label else ''}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nWrote {path.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
