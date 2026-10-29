"""Exploratory: are recorded WW2 results robust or fragile under the ambiguous windows of the
owner's decision 7j (snapshots/ww2/hindsight_ambiguous/, snapshots/ww2/hindsight_v1_ambiguous/)?

Not a rerun of any registered claim's verdict: the questions of recorded runs are asked again
from the member states of the layer, with the engines and readings of those runs (the test
files named below), and each answer is reported as robust (the same from every member) or
fragile (the members of each answer named), with wavefront.analysis.robust. Results are
written to reports/robustness_ww2.md by hand from this script's output.

- T13 (tests/ww2/scenarios/test_T13.py, v0 primary, symbolic engine): membership of WEST's
  kernel for balance_europe of the window states 1938Q2 to 1939Q1 (ticks 10 to 13, with their
  built-ins) under each aims_GER, and the departure quarter along the realized path over every
  choice of members.
- T9 (tests/ww2/scenarios/test_T09.py, v1, bounded checker with fixed strategies): its start
  state is 1939Q1.json, inside the italy_estranged window; each of the three tests' questions
  per member.

Usage: python scripts/robustness_ww2.py [t13|t9]
"""

from __future__ import annotations

import dataclasses
import itertools
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from models.ww2 import bounded  # noqa: E402
from models.ww2.hypotheses import (  # noqa: E402
    SNAPSHOTS_V1,
    quarter_tick,
    snapshot_data,
    snapshot_state,
)
from wavefront.analysis import robust  # noqa: E402
from wavefront.evidence import SnapshotStates, snapshot_to_states  # noqa: E402

LAYER_V0 = ROOT / "snapshots" / "ww2" / "hindsight_ambiguous"
LAYER_V1 = ROOT / "snapshots" / "ww2" / "hindsight_v1_ambiguous"


def layer_states(cm, quarter, aims_GER, *, snapshots, aims_USSR="defensive", **hidden):
    """The member states of a layer file, with its built-ins and the tick of ``quarter``
    (as ``snapshot_state(..., builtins=True)`` reads a canonical file)."""
    data = snapshot_data(
        quarter,
        builtins=True,
        snapshots=snapshots,
        aims_GER=aims_GER,
        aims_USSR=aims_USSR,
        **hidden,
    )
    res = snapshot_to_states(data, cm)
    i = cm.index["tick"]
    states = tuple(
        tuple(quarter_tick(quarter) if k == i else x for k, x in enumerate(s)) for s in res.states
    )
    return dataclasses.replace(res, states=states)


def t13() -> None:
    from models.ww2.v0 import model as v0_model
    from tests.ww2.scenarios.test_T13 import FILES, departure
    from wavefront.symbolic import encode, safe

    cm = v0_model.compile()
    t0 = time.time()
    enc = encode(cm)
    res = safe(enc, ["WEST"], enc.predicate("balance_europe"))
    print(f"T13 v0 kernel computed in {time.time() - t0:.0f} s")
    window = {p.stem for p in LAYER_V0.glob("*.json")}
    for aims in ("revisionist", "hegemonic"):
        per_file = []  # (tick, [(label, membership)])
        for q in [*FILES, "1939Q3"]:
            if q in window:
                members: SnapshotStates = layer_states(cm, q, aims, snapshots=LAYER_V0)
                r = robust(
                    f"T13 {q} in V",
                    members,
                    lambda s: "in" if res.contains(s) else "out",
                )
                print(f"T13 v0 {aims} {q} (tick {quarter_tick(q)}): {r.summary()}")
                per_file.append((quarter_tick(q), list(zip(r.labels, r.answers, strict=True))))
            else:
                st = snapshot_state(cm, q, aims, builtins=True)
                per_file.append(
                    (st[cm.index["tick"]], [("canonical", "in" if res.contains(st) else "out")])
                )
        departures: dict[object, list[str]] = {}
        for combo in itertools.product(*(opts for _, opts in per_file)):
            seen = [(t, m) for (t, _), (_, m) in zip(per_file, combo, strict=True)]
            d = departure(seen)
            label = "; ".join(
                f"{t}:{lab}"
                for (t, opts), (lab, _) in zip(per_file, combo, strict=True)
                if len(opts) > 1
            )
            departures.setdefault(d, []).append(label)
        verdict = "robust" if len(departures) == 1 else "fragile"
        print(
            f"T13 v0 {aims}: departure tick over {sum(map(len, departures.values()))} member "
            f"paths: {verdict}: {sorted(departures, key=str)}"
        )


def t9() -> None:
    from models.ww2.v1 import model
    from tests.ww2.scenarios import test_T09 as T9

    def members(cm, belief, alliance=True):
        ms = layer_states(cm, T9.START, "hegemonic", snapshots=LAYER_V1, aims_JPN="hegemonic")
        out = []
        for s in ms.states:
            s = list(s)
            i = cm.index["belief_GER"]
            s[i] = cm.variables[i].levels.index(belief)
            if alliance:
                s[cm.index["anglo_soviet_alliance"]] = 1
            out.append(tuple(s))
        # the canonical start is one of the members (checked)
        canon = T9.start(cm, belief, alliance)
        assert canon in out, "the canonical T9 start is not a member"
        return dataclasses.replace(ms, states=tuple(out))

    cm = model.compile(profile="deterred")
    plain = model.compile()
    assert SNAPSHOTS_V1.name == "hindsight_v1"
    for belief in T9.BELIEFS:
        t0 = time.time()
        m = members(cm, belief)
        rows = {
            "{WEST, USSR}": robust("joint", m, lambda s: T9.membership(cm, s, ["WEST", "USSR"])),
            "{WEST}": robust("west", m, lambda s: T9.membership(cm, s, ["WEST"])),
            "{USSR}": robust("ussr", m, lambda s: T9.membership(cm, s, ["USSR"])),
            "record (no alliance), {WEST, USSR}": robust(
                "record",
                members(cm, belief, alliance=False),
                lambda s: T9.membership(cm, s, ["WEST", "USSR"]),
            ),
            "{WEST, USSR} without deterred": robust(
                "without",
                members(plain, belief),
                lambda s: T9.membership(plain, s, ["WEST", "USSR"]),
            ),
        }
        for k, r in rows.items():
            print(f"T9 belief_GER {belief}: {k}: {r.summary()}")
        print(f"T9 belief_GER {belief}: {time.time() - t0:.0f} s")
    rest = {"WEST": T9.KEEP["WEST"], "USSR": T9.KEEP["USSR"], "JPN": [], "Nature": []}

    def region(s):
        forced, _ = bounded.forces(cm, s, T9.X, T9.TAKE)
        if forced:
            return "forced"
        blocked, _ = bounded.blocks(cm, s, T9.X, rest)
        return "blocked" if blocked else "undecided"

    for belief in ("will_not_fight", "uncertain"):
        r = robust("region", members(cm, belief), region)
        print(f"T9 otherwise contested, belief_GER {belief}: {r.summary()}")

    def first_ticks(s):
        resolve = bounded.reach_from(cm, s, 7, T9.V.belief_GER == "will_fight")
        taken = bounded.reach_from(cm, s, 7, T9.X)
        return (resolve.states[-1][cm.index["tick"]], taken.states[-1][cm.index["tick"]])

    r = robust("first ticks", members(cm, "will_not_fight", alliance=False), first_ticks)
    print(f"T9 will_fight first / Poland first taken (ticks): {r.summary()}")


if __name__ == "__main__":
    which = sys.argv[1:] or ["t13", "t9"]
    for name in which:
        {"t13": t13, "t9": t9}[name]()
