"""The research console's data layer (console/catalog.py, console/sim.py): every version can
be described, its claims are found, a state can be stepped, and the stores are written."""

from __future__ import annotations

import json

import pytest

from console import catalog, sim

VERSIONS = [v["id"] for v in catalog.VERSIONS]


@pytest.mark.parametrize("version", VERSIONS)
def test_every_version_is_described(version):
    d = catalog.describe(version)
    assert d["budget"]["actions"] == sum(
        1 for a in d["actors"] for x in a["actions"] if not x["idle"]
    )
    names = {v["name"] for v in d["variables"]}
    for a in d["actors"]:
        for x in a["actions"]:
            assert set(x["writes"]) <= names and set(x["reads"]) <= names | {"tick"}
            assert x["idle"] or x["source"], (a["name"], x["name"])
    assert d["endings"] and d["conditions"] and json.dumps(d)


def test_the_stages_name_what_each_version_adds():
    stages = {s["id"]: s for s in catalog.stages()}
    assert stages["v0.1"]["added_variables"] == ["adoption"]
    assert "O.acquire" in stages["v0.3"]["added_actions"]
    assert stages["v0.3"]["compared_with"] == "v0.1" and not stages["v0"]["added_actions"]


def test_knobs_are_cleaned_and_change_the_model():
    assert catalog.clean_knobs("v0.3", {"open_system": 0, "treaty_delay": "99", "x": 1}) == {
        "open_system": False,
        "pressure": True,
        "hosting": True,
        "open_adoption": True,
        "treaty_delay": 8,
    }
    closed = catalog.describe("v0.3", {"open_system": False})
    assert "O" not in [a["name"] for a in closed["actors"]]


@pytest.mark.parametrize("version,family,count", [("v0", "G", 30), ("v0.1", "D", 6)])
def test_claims_carry_their_parts(version, family, count):
    found = catalog.claims(version)
    assert len(found) == count and all(c["id"].startswith(family) for c in found)
    assert [c["id"] for c in found][:2] == [f"{family}1", f"{family}2"]
    d5 = {c["id"]: c for c in catalog.claims("v0.1")}["D5"]
    assert d5["status"] == "did not hold" and d5["parts"] and d5["predicted"]


def test_plain_names_come_from_the_glossary():
    assert catalog.plain("regime") == "Regulation strictness"
    assert catalog.plain("H.propose_treaty") == "Propose a treaty"
    assert catalog.plain("hosting_restricted") == "Service restricted"
    assert catalog.plain("stale") == ""  # a history record has no name of its own


def test_conditions_read_as_text():
    from wavefront.model import FALSE, V

    assert catalog.text((V.regime >= "mandatory") | FALSE) == "regime >= mandatory"
    assert catalog.text(~V.paused & V.cap.is_in(["agi"])) == "not (paused) and cap in {agi}"


@pytest.mark.parametrize("version", VERSIONS)
def test_a_state_can_be_stepped(version):
    q = {"version": version, "goal": "indifferent"}
    v = sim.begin(q)
    assert v["levels"]["a_objective"] == "indifferent" and not v["terminal"]
    assert v["conditions"]["balance_control"] is True
    move = [a["actions"][-1]["i"] for a in v["available"]]
    nxt = sim.step({**q, "state": v["state"], "move": move})
    assert nxt["levels"]["tick"] == "1" and len(nxt["played"]) == len(move)
    with pytest.raises(ValueError):
        sim.step({**q, "state": v["state"], "move": [99] * len(move)})
    with pytest.raises(ValueError):
        sim.view(catalog.compiled(version, None, {"a_objective": "aligned"})[1], [0, 1])


def test_srt_starts_as_a_copy_of_s0_and_overrides_reach_older_models():
    s = catalog.states()
    assert s["srt"]["levels"] == s["s0"]["levels"] and sim.origin_levels("srt") == {}
    q = {"version": "v0.1", "goal": "aligned", "overrides": {"cap": "agi", "o_cap": "agi"}}
    assert sim.begin(q)["levels"]["cap"] == "agi"  # o_cap does not exist in v0.1 and is skipped
    with pytest.raises(ValueError):
        sim.begin({"version": "v0.1", "overrides": {"cap": "godlike"}})


def test_the_stores_take_only_their_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(catalog, "RESEARCH", tmp_path)
    items = catalog.store_write("requests", {"text": "try v0.1 with strong oversight", "x": "y"})
    assert items[0]["id"] == 1 and items[0]["status"] == "new" and "x" not in items[0]
    items = catalog.store_write("requests", {"id": 1, "status": "done", "answer": "see report"})
    assert items[0]["status"] == "done" and items[0]["text"].startswith("try")
    assert json.loads((tmp_path / "requests.json").read_text())[0]["answer"] == "see report"


def test_the_findings_registry_names_no_bare_reachability():
    findings = catalog.store("findings")
    kinds = {"guarantee-zone reading", "no-return analysis", "assumption set"}
    assert findings and all(f["kind"] in kinds for f in findings)
    assert all((catalog.ROOT / f["evidence"]).exists() for f in findings)


def test_the_queue_plan_is_the_queue_scripts():
    import scripts.agi_v0_3_kernel_queue as script
    from tests.agi_v0_3.common import CLOSED, DEFAULT

    assert catalog.BUILDS == {"default": DEFAULT, "closed": CLOSED}
    assert catalog.PLAN_GOALS == script.ORDER
    assert [(c, n, list(a), t, list(p), lv) for c, n, _, a, t, p, lv in script.QUEUE] == [
        (c, n, a, t, p, lv) for c, n, a, t, p, lv in catalog.PLAN
    ]
    q = catalog.queue()
    assert len(q["items"]) == 48 and sum(q["counts"].values()) == 48


def test_the_owner_orders_the_waiting_zones(tmp_path, monkeypatch):
    monkeypatch.setattr(catalog, "ORDER_FILE", tmp_path / "queue_order.json")
    monkeypatch.setattr(catalog, "CLAIMS", tmp_path / "claims")
    plan = catalog.priority()
    assert len(plan) == 48 and len(set(plan)) == 48
    (tmp_path / "queue_order.json").write_text(json.dumps([plan[40], "gone", plan[3]]))
    assert catalog.priority()[:3] == [plan[40], plan[3], plan[0]]
    waiting = [e["id"] for e in catalog.queue()["items"] if e["status"] == "waiting"]
    if len(waiting) > 2:
        assert catalog.move(waiting[2], "top")[0] == waiting[2]
        assert catalog.move(waiting[2], "down")[:2] == [waiting[0], waiting[2]]
        assert [e["id"] for e in catalog.queue()["items"] if e["status"] == "waiting"][1] == (
            waiting[2]
        )
    with pytest.raises(ValueError):
        catalog.move("nonsense", "up")
    # A worker takes the first zone it may try, and no second worker takes the same one.
    first = catalog.pick(10_000, 1, "split")
    second = catalog.pick(10_000, 1, "split")
    if first is not None:
        assert second is None or second[2] != first[2]
        catalog.release(first[2])


def test_claim_runs_lists_the_planned_runs_that_have_not_started(tmp_path, monkeypatch):
    monkeypatch.setattr(catalog, "ROOT", tmp_path)
    monkeypatch.setattr(catalog, "RESEARCH", tmp_path)
    (tmp_path / "reports").mkdir()
    plan = [{"version": "agi_v0_4", "claim": c, "limit": g} for c, g in (("X7", 64), ("X8", 84))]
    (tmp_path / "claim_runs_plan.json").write_text(json.dumps(plan + [{"version": "other"}]))
    assert [w["claim"] for w in catalog.claim_runs()["waiting"]] == ["X7", "X8"]
    (tmp_path / "reports" / "agi_v0_4_chain.log").write_text(
        "=== 2026-11-24 00:38:25 PST X7 cap 64 GB\n"
    )
    assert [w["claim"] for w in catalog.claim_runs()["waiting"]] == ["X8"]


def test_the_last_parts_of_a_claim_stop_at_an_earlier_run(tmp_path, monkeypatch):
    monkeypatch.setattr(catalog, "ROOT", tmp_path)
    (tmp_path / "reports").mkdir()
    rows = [
        {"claim": "X3", "part": "a", "outcome": "not computed", "detail": "over the cap"},
        {"claim": "X7", "part": "a", "outcome": "met", "detail": {"seconds": {"g": 2.0}}},
        {"claim": "X3", "part": "a", "outcome": "met", "detail": {"seconds": {"g": 5.0}}},
        {"claim": "X3", "part": "b", "outcome": "not computed", "detail": "over the cap"},
    ]
    (tmp_path / "reports" / "agi_v0_4_parts.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows)
    )
    got = catalog._last_parts("agi_v0_4", "X3")
    assert [(r["part"], r["outcome"], r["seconds"]) for r in got] == [
        ("a", "met", 5.0),
        ("b", "not computed", None),
    ]


def test_request_runs_lists_the_requests_that_are_not_done(tmp_path, monkeypatch):
    monkeypatch.setattr(catalog, "RESEARCH", tmp_path)
    rows = [
        {"id": 901, "created": "2026-11-25 01:38", "status": "new", "text": "a", "version": "v0.4"},
        {
            "id": 902,
            "created": "2026-11-25 01:40",
            "status": "done",
            "text": "b",
            "version": "v0.1",
        },
    ]
    (tmp_path / "requests.json").write_text(json.dumps(rows))
    got = catalog.request_runs()
    assert [(r["id"], r["status"], r["running"]) for r in got] == [(901, "new", None)]
