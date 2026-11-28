"""Combine the two scorers' cards of an evidence review into its result
(research/evidence/rubric.json is the method, registered before any card was scored).

    PYTHONPATH=. python scripts/evidence_review.py research/evidence/2026-11-27

Reads ``cards.json``, ``scores_1.json`` and ``scores_2.json`` in the review's folder and
writes ``result.json``. Choices the rubric leaves open, fixed here before the scores of the
first review were read: a card on whose side the scorers disagree, or that either marks
"neither", is flagged and left out of the totals; a card's event is the collector's label
unless both scorers give the same other one; the proposal rule's "two consecutive reviews"
counts the reviews stored beside this one.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

PARTS = ("directness", "power", "reach", "reasoning", "corroboration")
CAP = 3
SHARE = 0.6


def combine(folder: Path) -> dict:
    root = folder.parent
    rubric = json.loads((root / "rubric.json").read_text(encoding="utf-8"))
    questions = json.loads((root / "questions.json").read_text(encoding="utf-8"))
    cards = json.loads((folder / "cards.json").read_text(encoding="utf-8"))
    passes = [
        {s["id"]: s for s in json.loads((folder / f"scores_{n}.json").read_text(encoding="utf-8"))}
        for n in (1, 2)
    ]
    out_cards = []
    for c in cards:
        one, two = passes[0][c["id"]], passes[1][c["id"]]
        totals = [sum(s[p] for p in PARTS) for s in (one, two)]
        why = []
        if one["side"] != two["side"]:
            why.append(f"the scorers disagree on the side ({one['side']}, {two['side']})")
        elif one["side"] == "neither":
            why.append("both scorers: supports neither side")
        elif one["side"] != c["side"]:
            why.append(f"both scorers place it on side {one['side']}, the collector on {c['side']}")
        if abs(totals[0] - totals[1]) >= 3:
            why.append(f"totals differ by {abs(totals[0] - totals[1])}")
        why += [
            f"{p} differs by {abs(one[p] - two[p])}" for p in PARTS if abs(one[p] - two[p]) >= 2
        ]
        agreed = one["side"] if one["side"] == two["side"] and one["side"] != "neither" else None
        event = one["event"] if one["event"] == two["event"] else c["event"]
        out_cards.append(
            {**c, "side": agreed, "collector_side": c["side"], "event": event}
            | {"score": sum(totals) / 2, "flags": why}
            | {"scores": [{p: s[p] for p in PARTS} | {"side": s["side"]} for s in (one, two)]}
            | {"reasons": [s["reasons"] for s in (one, two)]}
        )
    results = []
    for q in questions:
        mine = [c for c in out_cards if c["question"] == q["id"] and c["side"]]
        sides = {}
        for side in ("A", "B"):
            events: dict[str, dict] = {}
            for c in sorted((c for c in mine if c["side"] == side), key=lambda c: -c["score"]):
                e = events.setdefault(c["event"], {"event": c["event"], "score": c["score"]})
                e.setdefault("cards", []).append(c["id"])
                e.setdefault("actor", c["actor"])
                e.setdefault("audience", c["audience"])
                e.setdefault("top", c)
            per_actor: dict[str, int] = defaultdict(int)
            kept = []
            for e in sorted(events.values(), key=lambda e: -e["score"]):
                per_actor[e["actor"]] += 1
                e["counted"] = per_actor[e["actor"]] <= CAP
                kept.append(e)
            binding = any(
                e["counted"]
                and all(s["directness"] == 3 and s["power"] == 3 for s in e["top"]["scores"])
                for e in kept
            )
            by_audience = defaultdict(float)
            for e in kept:
                if e["counted"]:
                    by_audience[e["audience"]] += e["score"]
            for e in kept:
                del e["top"]
            sides[side] = {
                "text": q["sides"][side],
                "total": sum(e["score"] for e in kept if e["counted"]),
                "events": kept,
                "by_audience": dict(by_audience),
                "binding_event_by_a_deciding_actor": binding,
            }
        both = sides["A"]["total"] + sides["B"]["total"]
        share = sides["A"]["total"] / both if both else None
        audiences = {
            a: (sides["A"]["by_audience"].get(a, 0), sides["B"]["by_audience"].get(a, 0))
            for a in rubric["audiences"]
        }
        row = {"id": q["id"], "kind": q["kind"], "question": q["question"], "sides": sides}
        row |= {"share_of_side_A": share, "by_audience": audiences}
        if q["kind"] == "level question":
            lead = (
                "A"
                if (share or 0) >= SHARE
                else "B"
                if share is not None and 1 - share >= SHARE
                else None
            )
            earlier = sorted(p for p in root.iterdir() if p.is_dir() and p.name < folder.name)
            row["proposal"] = (
                "no change: neither side reaches 60% of the total"
                if lead is None
                else f"no change yet: side {lead} leads with "
                f"{max(share, 1 - share):.0%}"
                + (
                    ", with a binding event by a deciding actor"
                    if sides[lead]["binding_event_by_a_deciding_actor"]
                    else ", without a binding event by a deciding actor"
                )
                + f"; the rule needs two consecutive reviews and this is review {len(earlier) + 1}"
            )
            row["srt"] = q.get("srt")
        else:
            row["proposal"] = "an attitude question: no level is at stake"
        results.append(row)
    flagged = [c["id"] for c in out_cards if c["flags"]]
    return {"review": folder.name, "questions": results, "cards": out_cards, "flagged": flagged}


def main() -> None:
    folder = Path(sys.argv[1])
    got = combine(folder)
    (folder / "result.json").write_text(json.dumps(got, indent=1, ensure_ascii=False) + "\n")
    for q in got["questions"]:
        a, b = q["sides"]["A"]["total"], q["sides"]["B"]["total"]
        print(f"{q['id']}: A {a:.1f}, B {b:.1f}; {q['proposal']}")
    print(f"{len(got['flagged'])} of {len(got['cards'])} cards flagged")


if __name__ == "__main__":
    main()
