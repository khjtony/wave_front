"""The engine of a forked kernel job: the multi-core core by default, and the single core after
a multi-core attempt that ran out of memory (tests/agi/forked_engine.py)."""

from __future__ import annotations

import json
import os

import pytest

from tests.agi import forked_engine
from tests.agi.common import NotComputed
from wavefront.symbolic import sylvan_available


def test_chosen_engine():
    default = ("sylvan", min(12, os.cpu_count() or 1)) if sylvan_available() else ("c", 0)
    assert forked_engine.chosen("", "") == default
    assert forked_engine.chosen("c", "8") == ("c", 0)
    assert forked_engine.chosen("sylvan", "4") == ("sylvan", 4)
    assert forked_engine.attempts("sylvan", 12) == [("sylvan", 12), ("c", 0)]
    assert forked_engine.attempts("c", 0) == [("c", 0)]


def _core_or_memory_error(fails: tuple[str, ...]) -> str:
    core = os.environ["WAVEFRONT_BDD"]
    if core in fails:
        raise MemoryError(core)
    return core


@pytest.mark.parametrize("module", ["tests.agi_v0_3.kernels", "tests.agi_v0_4.kernels"])
def test_out_of_memory_on_the_multicore_core_is_tried_again_on_the_own_core(
    module, tmp_path, monkeypatch
):
    kernels = pytest.importorskip(module)
    monkeypatch.setattr(kernels, "READINGS", tmp_path / "readings.jsonl")
    monkeypatch.setattr(kernels, "PROGRESS", tmp_path / "progress")
    monkeypatch.setattr(kernels, "CORE", "sylvan")
    monkeypatch.setattr(kernels, "THREADS", 4)

    assert kernels.forked("q1", _core_or_memory_error, ("sylvan",)) == "c"
    assert kernels.forked("q2", _core_or_memory_error, ()) == "sylvan"
    with pytest.raises(NotComputed):
        kernels.forked("q3", _core_or_memory_error, ("sylvan", "c"))

    rows = [json.loads(x) for x in kernels.READINGS.read_text().splitlines()]
    assert [(r["question"], r["kind"], r["core"], r["threads"]) for r in rows] == [
        ("q1", "over", "sylvan", 4),
        ("q1", "ok", "c", None),
        ("q2", "ok", "sylvan", 4),
        ("q3", "over", "sylvan", 4),
        ("q3", "over", "c", None),
    ]
