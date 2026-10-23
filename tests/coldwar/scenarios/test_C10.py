"""C10: After 1965, further increases in `nuke` do not change kernel membership.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.

Reading (docs/cw_v0_decisions.md, R C10): for each year 1947 to 1991, the hindsight
state per hypothesis and K_J (symbolic). Each declared variable but the swept objective is
perturbed one level up and one down where legal (built-ins kept); a variable's score is its
number of K_J membership flips, a family's the highest of its members' (nuke: nuke_USA,
nuke_USSR; belief: the three belief variables; oversight). (a) from 1965, raising a nuke
variable from survivable or above flips nothing; (b) score(nuke) is below score(oversight)
and score(belief) in every year from 1966 and above both in every year to 1964 (1965
reported). Engine: symbolic.
"""

import pytest

from ..common import HYPS, Timer, compiled, hindsight, kernel

CLAIM = {
    "id": "C10",
    "from_state": "each year from 1965",
    "claim": (
        "once both principals hold survivable second strike, further increases in "
        "`nuke` do not change kernel membership; `oversight` and `belief` do"
    ),
    "expected": (
        "the sensitivity report (Q7) ranks `nuke` below `oversight` and `belief` after "
        "1965 and above them before"
    ),
    "sources": "Schelling 1966; Kristensen and Norris series",
}

FAMILIES = {
    "nuke": ("nuke_USA", "nuke_USSR"),
    "belief": ("belief_force_USA", "belief_USA_USSR", "belief_USSR_USA"),
    "oversight": ("oversight",),
}


def scores(cm, kj, s):
    base = kj.contains(s)
    out, up_flips = {}, {}
    for v in cm.variables:
        if v.origin != "var" or v.name == "aims_USSR":
            continue
        i = cm.index[v.name]
        flips = 0
        for d in (-1, 1):
            j = s[i] + d
            if 0 <= j < v.size:
                t = s[:i] + (j,) + s[i + 1 :]
                flipped = kj.contains(t) != base
                flips += flipped
                if d == 1:
                    up_flips[v.name] = flipped
        out[v.name] = flips
    return out, up_flips


@pytest.mark.slow
def test_C10():
    timer = Timer()
    print("\n[C10] engine: symbolic K_J, state perturbation of the hindsight states")
    results = {}
    for aims in HYPS:
        cm = compiled(aims)
        kj = kernel(aims, ("USA", "USSR"))
        a = True
        before = after = True
        for y in range(1947, 1992):
            s = hindsight(y, aims)
            sc, up = scores(cm, kj, s)
            fam = {f: max(sc[v] for v in vs) for f, vs in FAMILIES.items()}
            top = sorted(sc.items(), key=lambda kv: -kv[1])[:4]
            if y >= 1965:
                for v in FAMILIES["nuke"]:
                    if cm.state_dict(s)[v] in ("survivable", "overkill") and up.get(v):
                        a = False
            if y <= 1964:
                before = before and fam["nuke"] > fam["oversight"] and fam["nuke"] > fam["belief"]
            if y >= 1966:
                after = after and fam["nuke"] < fam["oversight"] and fam["nuke"] < fam["belief"]
            print(
                f"[C10]   aims_USSR={aims} {y}: in K_J {kj.contains(s)}; families {fam}; top {top}"
            )
        results[aims] = (a, before, after)
        print(
            f"[C10] aims_USSR={aims}: (a) {a}; (b) before 1965 {before}, "
            f"after 1965 {after} ({timer})"
        )
    assert any(all(v) for v in results.values()), results
