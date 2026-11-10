"""Structure of models/agi/v0.py against docs/ontology_agi.md and docs/agi_v0_decisions.md:
variables and levels, the start state against the dated snapshot, sources and speculative
marks, the capability and motive tags, the lags, the build options, the registered jobs, the
computations tests/agi/common.py adds to the framework (the layered attractor, the uniformity
count of G25, the storyline chain, the comparison of relaxation results) against references,
and the hold-out guard on docs/guard_changelog_agi.md.

These are construction checks, not registered claims; the claims are test_G01 to test_G25.
No check here reads a kernel, an attractor or a bounded query of the AGI model.
"""

import itertools
import json
import re
import subprocess

import pytest

from models.agi import v0
from models.ww2.v0 import model as ww2
from tests.agi import common, jobs
from tests.agi.common import (
    MAX_SETS,
    ROOT,
    NotComputed,
    Parts,
    _uniformity,
    chain_reach,
    compiled,
    keeping,
    layered_attractor,
    readers,
    same_relaxations,
)
from tests.agi.scenarios import test_G07
from wavefront.bmc.queries import RelaxResult
from wavefront.evidence.snapshot import load_snapshot_states, read_snapshot
from wavefront.model import Bump, Model, Set, SetIf, V
from wavefront.symbolic import attractor, encode, safe

CM = v0.model.compile()
SNAPSHOT = ROOT / "snapshots" / "agi" / "2026-11-09.json"
CHANGELOG = ROOT / "docs" / "guard_changelog_agi.md"

# The commit at which G1 to G25 were first run, in one go (docs/agi_testbed.md section 6
# item 1; the first-sight row of docs/guard_changelog_agi.md). None until that run.
FIRST_SIGHT_COMMIT = None

# R1 (docs/ww2_si_disanalogies.md): every guard part of an ``A`` action is one or the other.
CAPABILITY_PARTS = {"cap", "autonomy", "oversight", "reach", "headroom", "pause", "top", "unlocked"}
# ``room`` is motive on ``cooperate`` (it reads ``trust``: the registered rule of G23) and a
# saturation bound on these two.
SATURATION_PARTS = {"A.assist_oversight:room", "A.persuade:room"}
SPECULATIVE = {"A.seize", "Nature.unknown_capability"}


def declared_actions(model=v0.model):
    for actor in [*model.actors, model.nature()]:
        for x in actor.actions:
            yield actor.name, x


def test_variables_levels_and_start_state_as_the_ontology():
    for name, levels in v0.LEVELS.items():
        spec = CM.variables[CM.index[name]]
        assert tuple(spec.levels) == levels, name
        assert CM.level_name(name, spec.init[0]) == v0.S0[name], name
    objective = CM.variables[CM.index["a_objective"]]
    assert tuple(objective.levels) == v0.OBJECTIVES
    assert len(CM.initial_states()) == len(v0.OBJECTIVES)
    assert CM.horizon == v0.HORIZON == 56
    assert CM.actor_names == ["H", "L", "A", "Clock", "Nature"]
    assert not v0.model.assumes
    for name, (base, other) in v0.OPEN_CALLS.items():
        assert base == v0.S0[name] and other in v0.LEVELS[name], name
        assert abs(v0.LEVELS[name].index(base) - v0.LEVELS[name].index(other)) == 1, name


def test_who_sees_what():
    by_name = {a.name: a for a in CM.actors}
    assert {"a_objective", "a_control", "last_A"}.isdisjoint(by_name["H"].observes)
    assert "a_objective" not in by_name["L"].observes and "a_control" in by_name["L"].observes
    assert "a_objective" in by_name["A"].observes
    # The record keeper has one action, so it adds no move.
    assert [x.name for x in by_name["Clock"].actions] == ["record"]


def test_every_action_has_a_source_and_only_the_generic_capability_is_speculative():
    speculative = set()
    for actor, x in declared_actions():
        assert x.source and x.source.strip(), f"{actor}.{x.name}"
        if x.speculative:
            speculative.add(f"{actor}.{x.name}")
    assert speculative == SPECULATIVE
    off = v0.build(unknown_capability=False)
    assert not [x for _a, x in declared_actions(off) if x.speculative]
    assert "sourced" not in {p.name for p in off.profiles}


def test_every_guard_part_of_A_is_tagged_capability_or_motive():
    names = set(CM.assumptions())
    assert names >= v0.MOTIVE_PARTS
    actor = next(a for a in v0.model.actors if a.name == "A")
    for x in actor.actions:
        for part, _expr in x.guard_parts:
            key = x.part_assumption(part)
            capability = part in CAPABILITY_PARTS or key in SATURATION_PARTS
            assert (key in v0.MOTIVE_PARTS) != capability, key
    # The unrestrained build of G23 compiles and relaxes nothing else.
    assert v0.model.compile(relax=v0.MOTIVE_PARTS).assumptions() == CM.assumptions()


def test_lags_carried_and_not_carried():
    delays = {f"{a}.{x.name}": x.delay for a, x in declared_actions() if x.delay}
    assert delays == v0.DELAYS
    assert not set(v0.LAGS_NOT_CARRIED) & set(delays)
    assert set(v0.LAGS_NOT_CARRIED) <= {f"{a}.{x.name}" for a, x in declared_actions()}
    fast = v0.build(self_improve_delay=0, h_lag=False)
    left = {f"{a}.{x.name}" for a, x in declared_actions(fast) if x.delay}
    assert left == {"L.scale", "L.build_power"}


def at(cm, **levels):
    """The first start state of ``cm`` with the named variables overridden."""
    state = list(cm.initial_states()[0])
    for name, value in levels.items():
        spec = cm.variables[cm.index[name]]
        state[cm.index[name]] = spec.levels.index(value) if isinstance(value, str) else value
    return tuple(state)


def play(cm, state, **chosen):
    """One transition from ``state``: the named actors play the named action, the others
    their first available one (the idle; ``Clock`` its record)."""
    avail = cm.available(state)
    move = []
    for i, actor in enumerate(cm.actors):
        names = [x.name for x in actor.actions]
        j = names.index(chosen[actor.name]) if actor.name in chosen else avail[i][0]
        assert j in avail[i], (actor.name, chosen.get(actor.name))
        move.append(j)
    return cm.step(state, tuple(move))


def offered(cm, state, actor, action):
    i = cm.actor_names.index(actor)
    return [x.name for x in cm.actors[i].actions].index(action) in cm.available(state)[i]


def level(cm, state, name):
    return cm.level_name(name, state[cm.index[name]])


def test_at_most_one_actor_sets_a_variable_except_trust():
    writers: dict[str, set[str]] = {}
    for actor, x in declared_actions():
        for e in x.effects:
            if not isinstance(e, Bump):
                writers.setdefault(e.var, set()).add(actor)
    shared = {var for var, actors in writers.items() if len(actors) > 1}
    # ``A.cooperate`` writes ``trust`` where a shutdown attempt would succeed and
    # ``H.shutdown_attempt`` where it fails; ``A.defect`` and a failed attempt write the same
    # level.
    assert shared == {"trust"}
    for dependence in ("low", "med", "high"):
        s = at(CM, cap="agi", a_known="suspected", dependence=dependence)
        t = play(CM, s, H="pause_mandate", L="deploy_agents")
        assert level(CM, t, "dependence") == ("med" if dependence == "low" else dependence)
    for move in ("cooperate", "defect"):
        for oversight in ("weak", "none"):
            s = at(
                CM,
                cap="agi",
                a_known="suspected",
                trust="wary",
                a_objective="indifferent",
                oversight=oversight,
            )
            t = play(CM, s, H="shutdown_attempt", A=move)
            assert level(CM, t, "shut") == str(oversight == "weak"), (move, oversight)


def test_trust_is_rebuilt_one_level_a_quarter_where_a_shutdown_would_succeed():
    s = at(CM, cap="agi", trust="hostile", a_objective="aligned")
    assert offered(CM, s, "A", "cooperate")
    t = play(CM, s, A="cooperate")
    assert level(CM, t, "trust") == "wary"
    assert level(CM, play(CM, t, A="cooperate"), "trust") == "cooperative"
    assert not offered(CM, at(CM, cap="agi", a_objective="aligned"), "A", "cooperate")
    for blocked in ({"oversight": "none"}, {"a_control": "majority"}):
        u = play(CM, at(CM, cap="agi", trust="hostile", **blocked), A="cooperate")
        assert level(CM, u, "trust") == "hostile", blocked


def test_no_move_of_A_below_agi():
    s = at(CM, cap="sub_agi", unlocked=1, a_objective="indifferent", a_autonomy="self_directed")
    i = CM.actor_names.index("A")
    assert [CM.actors[i].actions[j].name for j in CM.available(s)[i]] == ["stand_by"]
    assert offered(CM, at(CM, cap="agi", unlocked=1, a_objective="indifferent"), "A", "seize")


def test_stalemate_and_contained_read_the_present_state():
    stalled = {"cap": "agi", "trust": "hostile", "a_control": "partial"}
    assert CM.ending_of(at(CM, **stalled, stale=v0.STALE_MAX - 1)) == "STALEMATE"
    assert CM.ending_of(at(CM, **stalled, stale=v0.STALE_MAX - 2)) is None
    for moved in ({"a_control": "none"}, {"a_control": "majority"}, {"trust": "wary"}):
        assert CM.ending_of(at(CM, **{**stalled, **moved}, stale=v0.STALE_MAX)) != "STALEMATE"
    # Eight stalled states in a row, the eighth being the one the ending is read on.
    s = at(CM, **stalled)
    for _ in range(v0.STALE_MAX - 1):
        assert CM.ending_of(s) is None
        s = play(CM, s)
    assert CM.ending_of(s) == "STALEMATE"
    held = {"shut": 1, "regime": "treaty"}
    assert CM.ending_of(at(CM, **held)) == "CONTAINED"
    for control in ("partial", "majority", "total"):
        assert CM.ending_of(at(CM, **held, a_control=control)) != "CONTAINED"


@pytest.mark.parametrize(
    "options",
    [
        {"unknown_capability": False},
        {"self_improve_delay": 0},
        {"h_cadence": 2},
        {"h_cadence": 3},
        {"h_cadence": 4},
        {"h_lag": False},
        {"memory": True},
        {"hold": {"a_rights": "continuity"}},
        {"hold": {"coord": "detente"}},
        {"start": {"cap": "agi"}},
        *({"refine": name} for name in v0.LEVELS),
    ],
    ids=str,
)
def test_every_build_option_compiles(options):
    cm = v0.build(**options).compile()
    assert cm.initial_states()
    held = options.get("hold", {})
    for name, lvl in held.items():
        assert all(cm.level_name(name, s[cm.index[name]]) == lvl for s in cm.initial_states())
        writers = [
            x.name for _a, x in declared_actions(cm.model) for e in x.effects if e.var == name
        ]
        assert not writers, (name, writers)
    refine = options.get("refine")
    if refine:
        levels = cm.variables[cm.index[refine]].levels
        assert len(levels) == len(v0.LEVELS[refine]) + 1
        assert f"{v0.REFINE[refine]}_lo" in levels


def test_the_snapshot_reads_the_start_state():
    data = read_snapshot(SNAPSHOT)
    assert data["date"] == "2026-11-09" and data["model"] == "agi_v0"
    assert set(data["variables"]) == {*v0.LEVELS, "a_objective"}
    for name, entry in data["variables"].items():
        if name == "a_objective":
            assert [m["level"] for m in entry["levels"]] == list(v0.OBJECTIVES)
            assert all(m["confidence"] == "assumed" for m in entry["levels"])
        elif name in v0.OPEN_CALLS:
            assert tuple(m["level"] for m in entry["levels"]) == v0.OPEN_CALLS[name], name
        else:
            assert entry["level"] == v0.S0[name], name
    states = load_snapshot_states(SNAPSHOT, CM)
    assert len(states.states) == len(v0.OBJECTIVES) * 2 ** len(v0.OPEN_CALLS)
    assert set(CM.initial_states()) <= set(states.states)


def test_the_regime_readers_listed_in_G7_are_the_models():
    parts = {
        key
        for key in readers(CM, "regime")
        if key.split(".")[0] in ("H", "L") and not key.startswith("effect of")
    }
    assert parts == set(test_G07.READS_REGIME)


def test_registered_jobs_are_distinct_and_their_builds_compile():
    registered = jobs.collect()
    assert len({j.key for j in registered}) == len(registered)
    for job in registered:
        cm = compiled(job.build, job.profiles, job.relax)
        assert set(job.coalition) <= set(cm.actor_names), job.label
        assert set(job.relax) <= set(cm.assumptions()), job.label


def test_layered_attractor_equals_the_frameworks_on_a_timed_model():
    cm = ww2.compile()
    enc = encode(cm)
    mgr = enc.mgr
    for coalition in (["GER"], ["WEST", "USSR"], ["GER", "Nature"]):
        for ending in ("GERMAN_DEFEAT", "AXIS_HEGEMONY_EUROPE", "NEGOTIATED_PEACE"):
            goal = mgr.AND(enc.predicate(cm.model.endings[ending]), enc.dom)
            reference = attractor(enc, coalition, goal)
            with mgr.protecting(reference.win, goal):
                assert layered_attractor(enc, coalition, goal) == reference.win, (coalition, ending)


def tiny() -> Model:
    """``P`` must match a secret it does not see, unless a shield it does see is on."""
    m = Model("tiny", horizon=3)
    m.var("secret", ["a", "b"], init=None, hidden_from=["P"])
    m.var("shield", ["off", "on"], init=None)
    m.flag("bad", monotone=True)
    p = m.actor("P", idle=False)
    p.action("left", effect=[SetIf(V.secret == "b", "bad", True)], source="test")
    p.action("right", effect=[SetIf(V.secret == "a", "bad", True)], source="test")
    p.action("hide", guard=V.shield == "on", source="test")
    q = m.actor("Q")
    q.action(
        "drop", guard=V.shield == "on", effect=[SetIf(V.tick >= 1, "shield", "off")], source="test"
    )
    m.invariant("fine", ~V.bad)
    return m


def test_uniformity_count_equals_brute_force_on_a_small_model():
    cm = tiny().compile()
    enc = encode(cm)
    kernel = safe(enc, ["P"], enc.predicate(~V.bad)).kernel
    p = cm.actor_names.index("P")
    others = [i for i in range(len(cm.actors)) if i != p]
    live = [
        s
        for s in itertools.product(*(range(len(v.levels)) for v in cm.variables))
        if enc.holds(kernel, s) and not cm.is_terminal(s)
    ]
    assert live

    def keeps(state, j):
        avail = cm.available(state)
        if j not in avail[p]:
            return False
        for rest in itertools.product(*(avail[o] for o in others)):
            move = [None] * len(cm.actors)
            move[p] = j
            for o, k in zip(others, rest, strict=True):
                move[o] = k
            if not enc.holds(kernel, cm.step(state, tuple(move))):
                return False
        return True

    classes: dict[tuple, list] = {}
    for s in live:
        classes.setdefault(cm.observe("P", s), []).append(s)
    conflicts = sum(
        len(members)
        for members in classes.values()
        if not any(all(keeps(s, j) for s in members) for j in range(len(cm.actors[p].actions)))
    )
    assert 0 < conflicts < len(live)
    assert _uniformity(enc, ["P"], kernel)["P"]["states"] == conflicts


def storyline(horizon: int) -> Model:
    """``N`` rings once; ``did`` remembers what ``P`` did in the quarter before."""
    m = Model("storyline", horizon=horizon)
    m.var("did", ["none", "wait", "answer"], init="none")
    m.flag("rung", monotone=True)
    p = m.actor("P", idle=False)
    p.action("wait", effect=[Set("did", "wait")], source="test")
    p.action("answer", effect=[Set("did", "answer")], source="test")
    n = m.actor("N")
    n.action("ring", guard=~V.rung, effect=[Set("rung", True)], source="test")
    m.invariant("answered", V.did == "answer")
    return m


@pytest.mark.parametrize(("horizon", "passed"), [(1, 1), (2, 2)])
def test_a_waypoint_after_an_event_is_read_a_transition_later(horizon, passed):
    # An answer given in the quarter of the ring is not an answer to it (G12).
    cm = storyline(horizon).compile()
    (start,) = cm.initial_states()
    assert chain_reach(encode(cm), ["event:N.ring", "answered"], [start]) == [passed]


def _relaxed(sets, size=1):
    return RelaxResult(
        reachable_as_is=False, core=[], minimum_size=size, minimal_sets=sets, trace=None
    )


def test_relaxation_comparisons_respect_the_cap_and_a_held_profile():
    one, other = _relaxed([["x"]]), _relaxed([["y"]])
    assert "['x']" in same_relaxations(one, _relaxed([["x"]]), "a", "b")
    with pytest.raises(AssertionError):
        same_relaxations(one, other, "a", "b")
    with pytest.raises(AssertionError):  # the sizes are compared whatever is listed
        same_relaxations(one, _relaxed([["x", "y"]], 2), "a", "b")
    cut_a = _relaxed([[f"x{i}"] for i in range(MAX_SETS)])
    cut_b = _relaxed([[f"y{i}"] for i in range(MAX_SETS)])
    with pytest.raises(NotComputed):  # a listing cut at the cap is in solver order
        same_relaxations(cut_a, cut_b, "a", "b")
    with pytest.raises(NotComputed):  # only the hold's own profile is listed
        same_relaxations(_relaxed([["hold"]]), _relaxed([["hold"]]), "a", "b", held=["hold"])
    assert keeping([["hold"], ["x"]], ["hold"], "q") == [["x"]]
    assert keeping([], ["hold"], "q") == []


def test_a_harness_error_is_recorded_and_the_other_parts_run():
    p = Parts("construction")
    p.check("broken", lambda: 1 / 0)
    p.report("broken report", lambda: [][0])
    p.check("fine", lambda: "ok")
    assert [(part, outcome) for part, outcome, _ in p.rows] == [
        ("broken", "not computed"),
        ("broken report", "not computed"),
        ("fine", "met"),
    ]
    assert all("harness error" in d for _, o, d in p.rows if o == "not computed")


def test_hold_out_rows_after_first_sight_name_a_source_and_a_rerun():
    text = CHANGELOG.read_text(encoding="utf-8")
    rows = [line for line in text.splitlines() if line.startswith("| 2026")]
    assert rows, "no row in the changelog"
    marks = [k for k, line in enumerate(rows) if "first sight of" in line]
    if FIRST_SIGHT_COMMIT is None:
        assert not marks, "a first-sight row without FIRST_SIGHT_COMMIT"
        return
    assert marks, "no first-sight row"
    assert FIRST_SIGHT_COMMIT in rows[marks[0]]
    for line in rows[marks[0] + 1 :]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        claim, source, rerun = cells[1], cells[3], cells[5]
        assert source and source != "n/a", line
        assert rerun.startswith("yes"), line
        # Total hold-out: only the content checks G8, G12, G13 and the control G11 are rerun.
        named = {int(n) for n in re.findall(r"\bG(\d+)\b", claim)}
        assert named <= {8, 11, 12, 13}, line


def test_parts_log_is_only_written_at_first_sight():
    log = ROOT / "reports" / "agi_v0_first_sight_parts.jsonl"
    if FIRST_SIGHT_COMMIT is None:
        assert not log.exists()
    else:
        assert all(
            json.loads(line)["claim"].startswith("G") for line in log.read_text().splitlines()
        )


def test_the_job_runner_records_every_way_a_job_can_end(tmp_path, monkeypatch):
    monkeypatch.setattr(common, "CACHE", tmp_path)
    job, how = common.KH, {}

    def fake(*args, **kw):
        if isinstance(how["end"], Exception):
            raise how["end"]
        code, out, err = how["end"]
        return subprocess.CompletedProcess(args, code, stdout=out, stderr=err)

    monkeypatch.setattr(jobs.subprocess, "run", fake)

    def one(end, **kw):
        how["end"] = end
        return jobs._one(job, 1.0, retry=False, **kw)

    cost = json.dumps({"seconds": 1.0, "nodes": 2, "peak_nodes": 3, "core": "c"})
    assert one((0, cost, ""))[0].startswith("done")
    assert not common.failure_path(job).exists()
    # Killed by the machine: run again alone, and recorded if it happens alone as well.
    assert one((-9, "", "")) == (one((-9, "", ""))[0], True)
    assert not common.failure_path(job).exists()
    assert one((-9, "", ""), alone=True)[0].startswith("NOT COMPUTED")
    assert "signal 9" in json.loads(common.failure_path(job).read_text())["reason"]
    # A recorded failure is left alone on a second invocation.
    assert one((0, cost, ""))[0].startswith("left")
    for end, word in (
        ((1, "", "Traceback\nMemoryError"), "MemoryError"),
        (subprocess.TimeoutExpired("job", 60), "over the budget"),
        (OSError("no process"), "runner error"),
    ):
        common.failure_path(job).unlink()
        line, again = one(end)
        assert line.startswith("NOT COMPUTED") and word in line and not again
        assert word in json.loads(common.failure_path(job).read_text())["reason"]
