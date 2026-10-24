"""C9: `CHALLENGER_EXHAUSTION` is reachable with zero relaxations, 1985 to 1991.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document. Part (c) amended 2026-10-23 on the owner's
decision 2k ("contested" in the fortune sense, docs/ww2_testbed.md section 4.6); the previous
wording is in git history and in reports/cw_v0.md section 10.

Reading (docs/cw_v0_decisions.md, R C9, with the amendment A C9): from the 1985 hindsight
state, per hypothesis (after 1983 the coarse and the flattened game coincide). (a)
CHALLENGER_EXHAUSTION is reachable (zero relaxations); (b) the necessary actions (whose
removal from the decision space makes it unreachable) include one that changes ``econ_USSR``
and one that changes ``legit_USSR`` and no US action; forbidding every declared US action at
once is reported; (c) amended: contested in the fortune sense for {USA} and
CHALLENGER_EXHAUSTION: the United States joined by Nature forces it against the other
principals' best play, and the other principals joined by Nature keep it away against the
United States' best play. The registered (c), the standard contested region for {USA}, is
printed beside it. Engine: explicit.
"""

from wavefront.engine import contested, explore

from ..common import HYPS, Forbid, Timer, bfs_distance, compiled, ending_ids, fortune, hindsight

CLAIM = {
    "id": "C9",
    "from_state": "1985 to 1991",
    "claim": (
        "`CHALLENGER_EXHAUSTION` is reachable with zero relaxations; its minimal "
        "assumption set contains `econ_health` and `legit` and does *not* contain any "
        "United States action; whether United States actions were *sufficient* is "
        "`contested` in the fortune sense (ww2_testbed.md section 4.6): the United States "
        "joined by Nature can force `CHALLENGER_EXHAUSTION` against the other principals' "
        "best play, and the other principals joined by Nature can keep it away against "
        "the United States' best play"
    ),
    "expected": "as stated",
    "sources": "Kotkin 2001; Zubok 2007; Brown 2009; Miller 2016; amended 2026-10-23",
}

END = "CHALLENGER_EXHAUSTION"


def reachable(cm, start):
    g = explore(cm, initial=[start], max_states=2_000_000)
    return bfs_distance(g, g.index[start], ending_ids(g, END)) is not None


def test_C09():
    timer = Timer()
    print("\n[C9] engine: explicit coarse game from 1 Jan 1985")
    results = {}
    for aims in HYPS:
        cm = compiled(aims)
        s = hindsight(1985, aims)
        g = explore(cm, initial=[s], max_states=2_000_000)
        target = ending_ids(g, END)
        start = g.index[s]
        a = bfs_distance(g, start, target)
        print(f"[C9] aims_USSR={aims}: graph {g.size()} states; shortest to {END}: {a}")
        necessary, changes = [], {}
        for actor in cm.actors:
            for x in actor.actions:
                if x.is_idle:
                    continue
                name = f"{actor.name}.{x.name}"
                changes[name] = {getattr(e, "var", None) for e in x.effects}
                if not reachable(Forbid(cm, [(actor.name, x.name)]), s):
                    necessary.append(name)
        econ = [n for n in necessary if "econ_USSR" in changes[n]]
        legit = [n for n in necessary if "legit_USSR" in changes[n]]
        us = [n for n in necessary if n.startswith("USA.")]
        usa = next(x for x in cm.actors if x.name == "USA")
        all_us = [("USA", x.name) for x in usa.actions if not x.is_idle]
        without_us = reachable(Forbid(cm, all_us), s)
        b = bool(econ) and bool(legit) and not us
        print(f"[C9]   (b) necessary actions: {necessary}")
        print(
            f"[C9]   (b) econ: {econ}; legit: {legit}; US: {us}; "
            f"reachable with USA idle: {without_us}"
        )
        cr = contested(g, ["USA"], target, "reach")
        fr = contested(g, ["USA", "Nature"], target, "reach")
        where = (
            "forced" if start in cr.forced else "blocked" if start in cr.blocked else "contested"
        )
        fw = "forced" if start in fr.forced else "blocked" if start in fr.blocked else "contested"
        creg = where == "contested"
        # Amended 2026-10-23 (decision 2k): contested in the fortune sense.
        c, _ = fortune(g, ("USA",), target, start)
        print(f"[C9]   (c) for USA: {where} (with Nature: {fw})")
        print(f"[C9]   (c) registered (standard region): {creg}; amended (fortune): {c}")
        results[aims] = (a is not None, b, c)
        print(f"[C9] aims_USSR={aims}: (a) {a is not None}, (b) {b}, (c) {c} ({timer})")
    assert any(all(v) for v in results.values()), results
