#!/usr/bin/env python3
"""
Unit 9, Milestone 5 — one trial of the capstone criteria. Run it three times.

    python run_capstone.py --trial 1
    python run_capstone.py --trial 2
    python run_capstone.py --trial 3

Each trial starts its OWN gunicorn (nothing reused between trials), drives it,
stops it, and writes results/capstone_trial_<n>.json with the real output.

    criterion 1  every /submit and /appeal line in access.log has a record
    criterion 2  six failure kinds each write a record (400 413 422 429 500 503)
    criterion 3  not here — it needs a person who isn't me
    criterion 4  cold first request ≤ 10 s; p95 of the next 100 ≤ 100 ms
    criterion 5  worker RSS after 500 /submit < 1,572,864 KB

The 500 can't be caused through the real server without adding a crash switch
to the service, so it runs in-process through Flask's test client with signal
two replaced by a function that raises. The 503 is real: a second gunicorn
started with a model name that doesn't exist and downloads switched off.
"""

import argparse
import datetime as dt
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import requests

import config
import eval_texts

ROOT = Path(__file__).parent
GUNICORN = str(Path(sys.executable).parent / "gunicorn")
TEXTS = eval_texts.CLEARLY_AI + eval_texts.CLEARLY_HUMAN + [eval_texts.LIGHTLY_EDITED_AI]
TARGETS = {"cold_s": 10.0, "p95_ms": 100.0, "rss_kb": 1_572_864, "records": 1.0}


def start(port, env_extra=None):
    env = {**os.environ, "PORT": str(port), **(env_extra or {})}
    proc = subprocess.Popen([GUNICORN, "-c", "gunicorn.conf.py", "app:app"], cwd=ROOT,
                            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    for _ in range(60):
        try:
            requests.get(f"{url}/ping", timeout=1)
        except requests.ConnectionError:
            time.sleep(0.5)
            continue
        break
    return proc, url


def stop(proc):
    proc.send_signal(signal.SIGTERM)
    proc.wait(timeout=30)


def worker_rss_kb(master_pid):
    """RSS of the gunicorn worker — the master's child, not the master."""
    kids = subprocess.run(["pgrep", "-P", str(master_pid)], capture_output=True,
                          text=True).stdout.split()
    out = subprocess.run(["ps", "-o", "pid=,rss=", "-p", ",".join(kids)],
                         capture_output=True, text=True).stdout.split()
    return {int(out[i]): int(out[i + 1]) for i in range(0, len(out), 2)}


def submit(url, text, creator):
    return requests.post(f"{url}/submit", json={"text": text, "creator_id": creator}, timeout=130)


def line_count(path):
    return sum(1 for _ in open(path, encoding="utf-8")) if path.exists() else 0


def access_lines(start_line):
    """/submit and /appeal lines written to access.log since start_line."""
    out = []
    for line in open(config.LOG_DIR / "access.log", encoding="utf-8").readlines()[start_line:]:
        stamp = dt.datetime.strptime(line[1:line.index("]")], "%d/%b/%Y:%H:%M:%S %z")
        request_line = line.split('"')[1]
        route = request_line.split()[1].split("?")[0]
        status = int(line.split('"')[2].split()[0])
        if route in ("/submit", "/appeal"):
            out.append({"time": stamp.timestamp(), "route": route, "status": status, "line": line.strip()})
    return out


def match_records(lines, records):
    """
    Criterion 1's matching: same route, same HTTP status, timestamps ≤ 2 s
    apart, each record used once. Reported two ways — `strict` uses only the
    `route` and `http_status` a record actually carries; `inferred` also reads
    a decision as /submit 200 and an appeal as /appeal 200, since those events
    can only come from there.
    """
    def fields(record, infer):
        route, status = record.get("route"), record.get("http_status")
        if infer and route is None and record.get("event") == "appeal":
            route = "/appeal"
        if infer and status is None and record.get("status") in ("decided", "under_review"):
            status = 200
        return route, status

    result = {}
    for mode in ("strict", "inferred"):
        unused = list(records)
        unmatched = []
        for line in lines:
            hit = next((r for r in unused
                        if fields(r, mode == "inferred") == (line["route"], line["status"])
                        and abs(dt.datetime.fromisoformat(r["timestamp"]).timestamp() - line["time"]) <= 2), None)
            if hit is None:
                unmatched.append(line["line"])
            else:
                unused.remove(hit)
        result[mode] = {"lines": len(lines), "matched": len(lines) - len(unmatched),
                        "unmatched": unmatched}
    return result


def forced_crash():
    """The 500, in-process: signal two replaced by a function that raises."""
    import app
    import stylometry

    real = stylometry.style_signal
    stylometry.style_signal = lambda text: 1 / 0
    try:
        response = app.app.test_client().post("/submit", json={
            "text": "Long enough to reach signal two, which is set to fail on purpose here.",
            "creator_id": "capstone_crash"})
    finally:
        stylometry.style_signal = real
    return response.status_code


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trial", type=int, required=True)
    parser.add_argument("--port", type=int, default=5070)
    args = parser.parse_args()
    t = args.trial
    tag = f"cap{t}"

    audit_start = line_count(config.AUDIT_LOG)
    access_start = line_count(config.LOG_DIR / "access.log")
    proc, url = start(args.port)
    statuses = {}

    # Criterion 4: the cold request, timed at the client.
    t0 = time.perf_counter()
    first = submit(url, TEXTS[0], f"{tag}_cold")
    cold_s = time.perf_counter() - t0

    # Criterion 4: the next 100, each its own creator so the limiter stays out.
    warm_ids = []
    for i in range(100):
        r = submit(url, TEXTS[i % len(TEXTS)], f"{tag}_warm_{i}")
        warm_ids.append(r.json()["content_id"])

    # Criteria 1 and 2: appeals, refusals and a rate-limit burst in the same run.
    for cid in warm_ids[:5]:
        statuses.setdefault("appeal_200", []).append(requests.post(
            f"{url}/appeal", json={"content_id": cid, "reasoning": f"capstone trial {t}"}).status_code)
    statuses["appeal_404"] = requests.post(f"{url}/appeal", json={
        "content_id": "no-such-id", "reasoning": "x"}).status_code
    statuses["400"] = requests.post(f"{url}/submit", json={"creator_id": f"{tag}_bad"}).status_code
    statuses["413"] = submit(url, "word " * 5000, f"{tag}_long").status_code
    statuses["422"] = submit(url, "Hi", f"{tag}_short").status_code
    statuses["429_burst"] = [submit(url, TEXTS[1], f"{tag}_burst").status_code for _ in range(6)]

    # Criterion 5: the rest of the way to 500 /submit, then read the worker.
    sent = 1 + 100 + 3 + 6
    for i in range(500 - sent):
        submit(url, TEXTS[i % len(TEXTS)], f"{tag}_load_{i}")
    rss = worker_rss_kb(proc.pid)
    stop(proc)

    records = [json.loads(l) for l in
               open(config.AUDIT_LOG, encoding="utf-8").readlines()[audit_start:]]
    # Decisions only: an appeal copies the original creator_id but isn't a submit.
    warm = sorted(r["duration_ms"] for r in records if r.get("status") == "decided"
                  and str(r.get("creator_id", "")).startswith(f"{tag}_warm_"))

    # Criterion 2's 503: a separate gunicorn whose model can't load.
    proc503, url503 = start(args.port + 1, {"AI201_DETECTOR_MODEL": "no-such-model",
                                            "HF_HUB_OFFLINE": "1"})
    statuses["503"] = submit(url503, TEXTS[0], f"{tag}_nomodel").status_code
    stop(proc503)
    statuses["500"] = forced_crash()

    all_records = [json.loads(l) for l in
                   open(config.AUDIT_LOG, encoding="utf-8").readlines()[audit_start:]]
    failure_records = {}
    for kind, creator in (("400", f"{tag}_bad"), ("413", f"{tag}_long"), ("422", f"{tag}_short"),
                          ("429", f"{tag}_burst"), ("503", f"{tag}_nomodel"), ("500", "capstone_crash")):
        rec = next((r for r in reversed(all_records) if r.get("creator_id") == creator
                    and r.get("event") in ("rejected", "error")), None)
        client = statuses["429_burst"][-1] if kind == "429" else statuses[kind]
        ok = bool(rec) and all(rec.get(f) is not None for f in ("event", "http_status", "duration_ms")) \
            and rec.get("http_status") == client
        failure_records[kind] = {"client_status": client, "passed": ok, "record": rec}

    report = {
        "trial": t,
        "when": dt.datetime.now().isoformat(timespec="seconds"),
        "statuses": statuses,
        "criterion_1": match_records(access_lines(access_start), all_records),
        "criterion_2": {"passed": sum(v["passed"] for v in failure_records.values()),
                        "of": 6, "kinds": failure_records},
        "criterion_4": {"cold_s": round(cold_s, 2), "first_status": first.status_code,
                        "warm_n": len(warm), "p95_ms": warm[94] if len(warm) >= 95 else None,
                        "median_ms": warm[len(warm) // 2] if warm else None,
                        "max_ms": warm[-1] if warm else None},
        "criterion_5": {"submits": 500, "worker_rss_kb": rss,
                        "below_target": all(v < TARGETS["rss_kb"] for v in rss.values())},
    }
    path = config.RESULTS_DIR / f"capstone_trial_{t}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    c1 = report["criterion_1"]
    print(f"trial {t}")
    print(f"  c1 records   strict {c1['strict']['matched']}/{c1['strict']['lines']}   "
          f"inferred {c1['inferred']['matched']}/{c1['inferred']['lines']}")
    print(f"  c2 failures  {report['criterion_2']['passed']}/6  "
          f"{ {k: v['client_status'] for k, v in failure_records.items()} }")
    c4 = report["criterion_4"]
    print(f"  c4 speed     cold {c4['cold_s']} s   p95 {c4['p95_ms']} ms   median {c4['median_ms']}   max {c4['max_ms']}")
    print(f"  c5 memory    worker RSS {rss} KB")
    print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
