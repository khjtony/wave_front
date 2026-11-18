"""Shared machinery for the AGI v0.2 claims (docs/agi_v0_2.html).

v0.2 is v0.1 with four switchable consequences of an open-weight release: ``recall`` (A),
``pressure`` (B), ``testing`` (C) and ``retrain`` (D). A build is named by its switches. The
bounded queries and the effort solver are v0's, the kernels are computed in forked processes
(``tests/agi_v0_2/kernels.py``); nothing reads or writes the caches of v0. Parts are logged to
``reports/agi_v0_2_parts.jsonl`` when ``WF_FIRST_SIGHT_AGI_V02=1``; the kernel parts run only
with ``WF_V02_KERNELS=1`` as well and read "not computed" otherwise.

The model is imported inside the functions, so that this registration could be committed
before ``models/agi_v0_2`` existed.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path

import pytest

from models.agi_v0_1 import v0_1
from tests.agi import common as agi
from wavefront.model.compile import CompiledModel

ROOT = Path(__file__).resolve().parents[2]
PARTS_LOG = ROOT / "reports" / "agi_v0_2_parts.jsonl"
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_AGI_V02") == "1"
KERNELS = os.environ.get("WF_V02_KERNELS") == "1"
first_sight = pytest.mark.skipif(
    not FIRST_SIGHT,
    reason="AGI v0.2 claims run on WF_FIRST_SIGHT_AGI_V02=1 (docs/agi_v0_2.html section 7)",
)
OBJECTIVES = v0_1.OBJECTIVES
NON_ALIGNED = tuple(o for o in OBJECTIVES if o != "aligned")
K = 24
CONSEQUENCES = ("recall", "pressure", "testing", "retrain")
OFF: dict[str, bool] = dict.fromkeys(CONSEQUENCES, False)
ON: dict[str, bool] = dict.fromkeys(CONSEQUENCES, True)
KERNELS_LATER = "kernel part: run with WF_V02_KERNELS=1 after the timing probe"


def only(consequence: str) -> dict[str, bool]:
    """The build with one consequence on."""
    return {**OFF, consequence: True}


def key(switches: Mapping[str, bool]) -> str:
    return json.dumps(dict(switches), sort_keys=True)


def name(switches: Mapping[str, bool]) -> str:
    on = [c for c in CONSEQUENCES if switches[c]]
    return "all off" if not on else "all on" if len(on) == len(CONSEQUENCES) else "+".join(on)


@lru_cache(maxsize=None)
def _fixed(objective: str, switches: str) -> CompiledModel:
    from models.agi_v0_2 import v0_2

    model = v0_2.build(start={"a_objective": objective}, **json.loads(switches))
    return model.compile(profile=v0_2.OBJECTIVE_PROFILES)


def fixed(objective: str, switches: Mapping[str, bool]) -> CompiledModel:
    """The build of ``switches`` with the start objective fixed, ``A`` under its profile: the
    three objective profiles at once, each conditional on its objective, so that the profile
    follows the objective when retraining changes it."""
    return _fixed(objective, key(switches))


class Parts(agi.Parts):
    """The parts of a v0.2 claim, logged apart from v0's and v0.1's."""

    def _add(self, part: str, outcome: str, detail: object) -> None:
        self.rows.append((part, outcome, str(detail)))
        if FIRST_SIGHT:
            PARTS_LOG.parent.mkdir(exist_ok=True)
            row = {"claim": self.claim, "part": part, "outcome": outcome, "detail": detail}
            with PARTS_LOG.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    def kernel(self, part: str, fn) -> object:
        """A part that needs a kernel: checked with ``WF_V02_KERNELS=1``, else not computed."""
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
