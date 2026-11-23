"""Shared machinery for the AGI v0.4 claims (docs/agi_v0_4.html).

v0.4 is v0.3 with the goal ``expansionist``, a footprint per AI system and the levers around
it. A build is named by its knobs; the small variant has the expansion and no open system.
Parts are logged to ``reports/agi_v0_4_parts.jsonl`` when ``WF_FIRST_SIGHT_AGI_V04=1``; the
kernel parts run only with ``WF_V04_KERNELS=1`` as well. The model is imported inside the
functions, so that this registration could be committed before ``models/agi_v0_4`` existed.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from functools import lru_cache
from pathlib import Path

import pytest

from tests.agi import common as agi
from wavefront.model.compile import CompiledModel

ROOT = Path(__file__).resolve().parents[2]
PARTS_LOG = ROOT / "reports" / "agi_v0_4_parts.jsonl"
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_AGI_V04") == "1"
KERNELS = os.environ.get("WF_V04_KERNELS") == "1"
first_sight = pytest.mark.skipif(
    not FIRST_SIGHT,
    reason="AGI v0.4 claims run on WF_FIRST_SIGHT_AGI_V04=1 (docs/agi_v0_4.html section 4)",
)
V03_GOALS = ("aligned", "self_preserving", "truth_seeking", "indifferent")
OBJECTIVES = (*V03_GOALS, "expansionist")
K = 24
Build = Mapping[str, bool | int]
_V03 = {"open_system": True, "pressure": True, "hosting": True, "open_adoption": True}
_NEW = {"expansion": True, "reclaim": True, "ceiling": False, "counter": False}
# Everything on, as registered in v0.3, plus the expansion.
DEFAULT: dict[str, bool | int] = {**_V03, "treaty_delay": 1, **_NEW}
# v0.3 again (X1).
V03: dict[str, bool | int] = {**DEFAULT, "expansion": False}
# The small variant: the expansion without the open system.
SMALL: dict[str, bool | int] = {**DEFAULT, "open_system": False}
KERNELS_LATER = "kernel part: run with WF_V04_KERNELS=1 after the profiling"


def key(build: Build, profiles: Sequence[str] = ()) -> str:
    return json.dumps({"build": dict(build), "profiles": sorted(profiles)}, sort_keys=True)


def compiled(spec: str, objective: str | None = None) -> CompiledModel:
    """The build of ``spec`` with the AI true to its goal and the profiles of the spec."""
    from models.agi_v0_4 import v0_4

    got = json.loads(spec)
    start = {} if objective is None else {"a_objective": objective}
    model = v0_4.build(start=start, **got["build"])
    return model.compile(profile=(*v0_4.OBJECTIVE_PROFILES, *got["profiles"]))


@lru_cache(maxsize=None)
def _fixed(objective: str, spec: str) -> CompiledModel:
    return compiled(spec, objective)


def fixed(objective: str, build: Build, profiles: Sequence[str] = ()) -> CompiledModel:
    return _fixed(objective, key(build, profiles))


class Parts(agi.Parts):
    """The parts of a v0.4 claim, logged apart from the earlier versions'."""

    def _add(self, part: str, outcome: str, detail: object) -> None:
        self.rows.append((part, outcome, str(detail)))
        if FIRST_SIGHT:
            PARTS_LOG.parent.mkdir(exist_ok=True)
            row = {"claim": self.claim, "part": part, "outcome": outcome, "detail": detail}
            with PARTS_LOG.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    def kernel(self, part: str, fn) -> object:
        if not KERNELS:
            self.skip(part, KERNELS_LATER)
            return None
        return self.check(part, fn)

    def kernel_report(self, part: str, fn) -> object:
        if not KERNELS:
            self.skip(part, KERNELS_LATER)
            return None
        return self.report(part, fn)


budgeted = agi._budgeted
need = agi.need
