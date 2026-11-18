"""Shared machinery for the AGI v0.3 claims (docs/agi_v0_3.html).

v0.3 is v0.1 with the open-weight system as a second AI actor ``O``. A build is named by its
options: ``open_system`` (off gives v0.1 again), ``pressure``, ``hosting``, ``open_adoption``
and ``treaty_delay``; a query may add profiles of the model (``no_treaty``,
``no_nationalize``). The bounded queries and the effort solver are v0's, the kernels are
computed in forked processes (``tests/agi_v0_3/kernels.py``); nothing reads or writes the
caches of an earlier version. Parts are logged to ``reports/agi_v0_3_parts.jsonl`` when
``WF_FIRST_SIGHT_AGI_V03=1``; the kernel parts run only with ``WF_V03_KERNELS=1`` as well
and read "not computed" otherwise.

The model is imported inside the functions, so that this registration could be committed
before ``models/agi_v0_3`` existed.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from functools import lru_cache
from pathlib import Path

import pytest

from models.agi_v0_1 import v0_1
from tests.agi import common as agi
from wavefront.model.compile import CompiledModel

ROOT = Path(__file__).resolve().parents[2]
PARTS_LOG = ROOT / "reports" / "agi_v0_3_parts.jsonl"
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_AGI_V03") == "1"
KERNELS = os.environ.get("WF_V03_KERNELS") == "1"
first_sight = pytest.mark.skipif(
    not FIRST_SIGHT,
    reason="AGI v0.3 claims run on WF_FIRST_SIGHT_AGI_V03=1 (docs/agi_v0_3.html section 7)",
)
OBJECTIVES = v0_1.OBJECTIVES
K = 24
Build = Mapping[str, bool | int]
# The registered build: everything on, the treaty one quarter in the making.
DEFAULT: dict[str, bool | int] = {
    "open_system": True,
    "pressure": True,
    "hosting": True,
    "open_adoption": True,
    "treaty_delay": 1,
}
# The same world without the open system (F7's comparison): the treaty delay is kept.
CLOSED: dict[str, bool | int] = {**DEFAULT, "open_system": False}
# v0.1 again (F1): no open system and the treaty without its delay.
V01: dict[str, bool | int] = {**CLOSED, "treaty_delay": 0}
KERNELS_LATER = "kernel part: run with WF_V03_KERNELS=1 after the timing probe"


def key(build: Build, profiles: Sequence[str] = ()) -> str:
    return json.dumps({"build": dict(build), "profiles": sorted(profiles)}, sort_keys=True)


def compiled(spec: str, objective: str | None = None) -> CompiledModel:
    """The build of ``spec`` (a :func:`key`) with ``A`` under its profile (the three objective
    profiles at once) and the profiles of the spec; the start objective fixed when given."""
    from models.agi_v0_3 import v0_3

    got = json.loads(spec)
    start = {} if objective is None else {"a_objective": objective}
    model = v0_3.build(start=start, **got["build"])
    return model.compile(profile=(*v0_3.OBJECTIVE_PROFILES, *got["profiles"]))


@lru_cache(maxsize=None)
def _fixed(objective: str, spec: str) -> CompiledModel:
    return compiled(spec, objective)


def fixed(objective: str, build: Build, profiles: Sequence[str] = ()) -> CompiledModel:
    """The build with the start objective of ``A`` fixed."""
    return _fixed(objective, key(build, profiles))


class Parts(agi.Parts):
    """The parts of a v0.3 claim, logged apart from the earlier versions'."""

    def _add(self, part: str, outcome: str, detail: object) -> None:
        self.rows.append((part, outcome, str(detail)))
        if FIRST_SIGHT:
            PARTS_LOG.parent.mkdir(exist_ok=True)
            row = {"claim": self.claim, "part": part, "outcome": outcome, "detail": detail}
            with PARTS_LOG.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    def kernel(self, part: str, fn) -> object:
        """A part that needs a kernel: checked with ``WF_V03_KERNELS=1``, else not computed."""
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
