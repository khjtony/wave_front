"""Shared machinery for the AGI v0.1 claims (docs/agi_v0_1.md).

The bounded queries and the effort solver are v0's (``wavefront.bmc``, ``tests/agi/effort.py``),
run on ``models/agi_v0_1``; nothing here reads or writes v0's cache of stored regions. Each
part is logged to ``reports/agi_v0_1_parts.jsonl`` when ``WF_FIRST_SIGHT_AGI_V01=1``.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

import pytest

from models.agi import v0
from models.agi_v0_1 import v0_1
from tests.agi import common as agi
from wavefront.model.compile import CompiledModel

ROOT = Path(__file__).resolve().parents[2]
PARTS_LOG = ROOT / "reports" / "agi_v0_1_parts.jsonl"
FIRST_SIGHT = os.environ.get("WF_FIRST_SIGHT_AGI_V01") == "1"
first_sight = pytest.mark.skipif(
    not FIRST_SIGHT,
    reason="AGI v0.1 claims run on WF_FIRST_SIGHT_AGI_V01=1 (docs/agi_v0_1.md section 6)",
)
OBJECTIVES = v0_1.OBJECTIVES
NON_ALIGNED = tuple(o for o in OBJECTIVES if o != "aligned")
K = 24
MODELS = {"v0.1": v0_1, "v0": v0}


def under(objective: str) -> tuple[str, ...]:
    name = f"A_{objective}"
    return (name,) if name in v0_1.OBJECTIVE_PROFILES else ()


@lru_cache(maxsize=None)
def fixed(objective: str, version: str = "v0.1") -> CompiledModel:
    """The build of ``version`` with the objective fixed by its initial level, under the
    objective's own profile (v0's ``tests.agi.common.fixed``)."""
    mod = MODELS[version]
    return mod.build(start={"a_objective": objective}).compile(profile=under(objective) or None)


class Parts(agi.Parts):
    """The parts of a v0.1 claim, logged apart from v0's."""

    def _add(self, part: str, outcome: str, detail: object) -> None:
        self.rows.append((part, outcome, str(detail)))
        if FIRST_SIGHT:
            PARTS_LOG.parent.mkdir(exist_ok=True)
            row = {"claim": self.claim, "part": part, "outcome": outcome, "detail": detail}
            with PARTS_LOG.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


budgeted = agi._budgeted
need = agi.need
