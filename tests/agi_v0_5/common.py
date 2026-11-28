"""Shared machinery for the AGI v0.5 claims (docs/agi_v0_5.html).

v0.5 is v0.4 with a clock of two-month steps that ends with 2032. A build is named by its
knobs; ``step_months=3`` with ``study_quarters=56`` is v0.4's clock.
Parts are logged to ``reports/agi_v0_5_parts.jsonl`` when ``WF_FIRST_SIGHT_AGI_V05=1``; the
kernel parts run only with ``WF_V05_KERNELS=1`` as well. The model is imported inside the
functions, so that this registration could be committed before ``models/agi_v0_5`` existed.
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
PARTS_LOG = ROOT / "reports" / "agi_v0_5_parts.jsonl"
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_AGI_V05") == "1"
KERNELS = os.environ.get("WF_V05_KERNELS") == "1"
first_sight = pytest.mark.skipif(
    not FIRST_SIGHT,
    reason="AGI v0.5 claims run on WF_FIRST_SIGHT_AGI_V05=1 (docs/agi_v0_5.html section 4)",
)
V03_GOALS = ("aligned", "self_preserving", "truth_seeking", "indifferent")
OBJECTIVES = (*V03_GOALS, "expansionist")
# The search length: the whole study of v0.5 (36 two-month steps); 24 quarters on the builds
# with v0.4's clock.
K = 36
K_V04 = 24
Build = Mapping[str, bool | int]
_V04 = {"open_system": True, "pressure": True, "hosting": True, "open_adoption": True}
_V04 |= {"treaty_delay": 1, "expansion": True, "reclaim": True, "ceiling": False, "counter": False}
# The registered build: two-month steps to the end of 2032, both AI systems.
DEFAULT: dict[str, bool | int] = {**_V04, "step_months": 2, "study_quarters": 24}
# The small variant: no open system.
SMALL: dict[str, bool | int] = {**DEFAULT, "open_system": False}
# v0.4's clock again (Y1): quarters to 2040 Q4.
V04: dict[str, bool | int] = {**_V04, "step_months": 3, "study_quarters": 56}
V04_SMALL: dict[str, bool | int] = {**V04, "open_system": False}
V04_NO_EXPANSION: dict[str, bool | int] = {**V04, "expansion": False}
KERNELS_LATER = "kernel part: run with WF_V05_KERNELS=1 after the profiling"


def key(build: Build, profiles: Sequence[str] = ()) -> str:
    return json.dumps({"build": dict(build), "profiles": sorted(profiles)}, sort_keys=True)


def compiled(spec: str, objective: str | None = None) -> CompiledModel:
    """The build of ``spec`` with the AI true to its goal and the profiles of the spec."""
    from models.agi_v0_5 import v0_5

    got = json.loads(spec)
    start = {} if objective is None else {"a_objective": objective}
    model = v0_5.build(start=start, **got["build"])
    return model.compile(profile=(*v0_5.OBJECTIVE_PROFILES, *got["profiles"]))


@lru_cache(maxsize=None)
def _fixed(objective: str, spec: str) -> CompiledModel:
    return compiled(spec, objective)


def fixed(objective: str, build: Build, profiles: Sequence[str] = ()) -> CompiledModel:
    return _fixed(objective, key(build, profiles))


class Parts(agi.Parts):
    """The parts of a v0.5 claim, logged apart from the earlier versions'."""

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
