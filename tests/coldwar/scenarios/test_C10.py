"""C10: After 1965, further increases in `nuke` do not change kernel membership.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document. Part (b) amended 2026-10-23 on the owner's
decision 2n (oversight and belief measured by their effect on reachability and on the
unilateral kernels, not on the joint kernel); the previous wording is in git history and in
reports/cw_v0.md section 11.

Reading (docs/cw_v0_decisions.md, R C10, with the amendment A C10): for each year 1947 to
1991, the hindsight state per hypothesis. Each declared variable but the swept objective is
perturbed one level up and one down where legal (built-ins kept). (a) unchanged: from 1965,
raising a nuke variable from survivable or above flips no K_J membership (K_J the symbolic
joint kernel of balance_cw). (b) amended: a perturbation counts for its variable when it
changes the state's membership in K_USA or in K_USSR (the unilateral kernels of
balance_cw) or its shortest trace to GENERAL_WAR or ACCIDENTAL_WAR (the rank in the
attractor of every actor, Nature included, over the whole coarse domain); a variable's score
is its number of counting perturbations, a family's the highest of its members' (nuke:
nuke_USA, nuke_USSR; belief: the three belief variables; oversight); score(nuke) is below
score(oversight) and score(belief) in every year from 1966 and above both in every year to
1964 (1965 reported). The registered (b), on K_J membership flips, is printed beside it.
Engine: symbolic.
"""

import pytest

from ..common import HYPS, Timer, compiled, hindsight, kernel, reach_all

CLAIM = {
    "id": "C10",
    "from_state": "each year from 1965",
    "claim": (
        "once both principals hold survivable second strike, further increases in "
        "`nuke` do not change kernel membership; `oversight` and `belief` do change "
        "the state's membership in the unilateral kernels `⟨⟨USA⟩⟩□balance_cw` and "
        "`⟨⟨USSR⟩⟩□balance_cw` or its shortest trace to `GENERAL_WAR` or "
        "`ACCIDENTAL_WAR`"
    ),
    "expected": (
        "the sensitivity report (Q7), scoring a variable by the one-level perturbations "
        "that change unilateral-kernel membership or the shortest trace to the adverse "
        "endings, ranks `nuke` below `oversight` and `belief` after 1965 and above them "
        "before"
    ),
    "sources": "Schelling 1966; Kristensen and Norris series; amended 2026-10-23",
}

FAMILIES = {
    "nuke": ("nuke_USA", "nuke_USSR"),
    "belief": ("belief_force_USA", "belief_USA_USSR", "belief_USSR_USA"),
    "oversight": ("oversight",),
}


def perturbations(cm, s):
    """``(variable, direction, perturbed state)`` for every declared variable but the swept
    objective, one level up and one down where legal."""
    for v in cm.variables:
        if v.origin != "var" or v.name == "aims_USSR":
            continue
        i = cm.index[v.name]
        for d in (-1, 1):
            j = s[i] + d
            if 0 <= j < v.size:
                yield v.name, d, s[:i] + (j,) + s[i + 1 :]


def scores(cm, kj, s):
    """The registered scores: K_J membership flips."""
    base = kj.contains(s)
    out, up_flips = {v.name: 0 for v in cm.variables}, {}
    for name, d, t in perturbations(cm, s):
        flipped = kj.contains(t) != base
        out[name] += flipped
        if d == 1:
            up_flips[name] = flipped
    return out, up_flips


def measures(aims, ku, kr, s):
    return (ku.contains(s), kr.contains(s), reach_all(aims, "adverse").rank(s))


def amended_scores(aims, cm, ku, kr, s):
    """Amended 2026-10-23 (decision 2n): perturbations that change unilateral-kernel
    membership or the shortest trace to the adverse endings."""
    base = measures(aims, ku, kr, s)
    out = {v.name: 0 for v in cm.variables}
    for name, _, t in perturbations(cm, s):
        out[name] += measures(aims, ku, kr, t) != base
    return out


def rank_ok(fam, y, before, after):
    if y <= 1964:
        before = before and fam["nuke"] > fam["oversight"] and fam["nuke"] > fam["belief"]
    if y >= 1966:
        after = after and fam["nuke"] < fam["oversight"] and fam["nuke"] < fam["belief"]
    return before, after


@pytest.mark.slow
def test_C10():
    timer = Timer()
    print("\n[C10] engine: symbolic kernels, state perturbation of the hindsight states")
    results = {}
    for aims in HYPS:
        cm = compiled(aims)
        kj = kernel(aims, ("USA", "USSR"))
        ku, kr = kernel(aims, ("USA",)), kernel(aims, ("USSR",))
        a = True
        before = after = True
        before_r = after_r = True
        for y in range(1947, 1992):
            s = hindsight(y, aims)
            sc, up = scores(cm, kj, s)
            fam_r = {f: max(sc[v] for v in vs) for f, vs in FAMILIES.items()}
            am = amended_scores(aims, cm, ku, kr, s)
            fam = {f: max(am[v] for v in vs) for f, vs in FAMILIES.items()}
            top = sorted(am.items(), key=lambda kv: -kv[1])[:4]
            if y >= 1965:
                for v in FAMILIES["nuke"]:
                    if cm.state_dict(s)[v] in ("survivable", "overkill") and up.get(v):
                        a = False
            before_r, after_r = rank_ok(fam_r, y, before_r, after_r)
            before, after = rank_ok(fam, y, before, after)
            print(
                f"[C10]   aims_USSR={aims} {y}: in K_J {kj.contains(s)}, K_USA "
                f"{ku.contains(s)}, K_USSR {kr.contains(s)}; shortest to adverse "
                f"{reach_all(aims, 'adverse').rank(s)}; families {fam} "
                f"(registered, K_J flips: {fam_r}); top {top}"
            )
        results[aims] = (a, before, after)
        print(
            f"[C10] aims_USSR={aims}: (a) {a}; (b) amended: before 1965 {before}, "
            f"after 1965 {after}; registered: before {before_r}, after {after_r} ({timer})"
        )
    assert any(all(v) for v in results.values()), results
