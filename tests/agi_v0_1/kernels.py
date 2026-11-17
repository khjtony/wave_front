"""The kernels of D5 and D6 (docs/agi_v0_1.md section 5, part B), computed in the claim's own
process with v0's engine settings (FORCE order, deferred collection: ``heavy_encoding``) and
read at named states. Nothing is cached: v0's store is never read or written.

``A`` "under its profile" is every objective profile at once (v0's ``P``); with the objective a
free initial level, one kernel answers for every objective. An address-space cap from
``WF_V01_MEMORY_GB`` (default 26) bounds each process; over it the part reads not computed.
"""

from __future__ import annotations

import os
import resource
import time
from functools import lru_cache

from models.agi_v0_1 import v0_1
from tests.agi.common import NotComputed, heavy_encoding, target_bdd
from wavefront.model.compile import CompiledModel
from wavefront.symbolic import safe

P = tuple(v0_1.OBJECTIVE_PROFILES)
U: tuple[str, ...] = ()
MEMORY_GB = int(os.environ.get("WF_V01_MEMORY_GB", "26"))


def _cap() -> None:
    cap = MEMORY_GB << 30
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    if soft == resource.RLIM_INFINITY or soft > cap:
        resource.setrlimit(resource.RLIMIT_AS, (cap, hard))


@lru_cache(maxsize=None)
def game(profiles: tuple[str, ...]) -> CompiledModel:
    return v0_1.build().compile(profile=profiles or None)


@lru_cache(maxsize=None)
def kernel(coalition: tuple[str, ...], target: str, profiles: tuple[str, ...]):
    """``(encoding, kernel BDD, seconds, peak nodes)`` of ``⟨⟨coalition⟩⟩□target``."""
    _cap()
    cm = game(profiles)
    t0 = time.perf_counter()
    try:
        enc = heavy_encoding(cm)
        f = safe(enc, list(coalition), target_bdd(enc, target)).kernel
        enc.mgr.protect(f)
    except MemoryError as exc:
        raise NotComputed(f"over the cap of {MEMORY_GB} GB: {exc}") from exc
    return enc, f, round(time.perf_counter() - t0, 1), enc.mgr.stats()["peak_nodes"]


def start(cm: CompiledModel, objective: str) -> tuple[int, ...]:
    states = [s for s in cm.initial_states() if cm.state_dict(s)["a_objective"] == objective]
    if len(states) != 1:
        raise RuntimeError(f"{len(states)} initial states under {objective}")
    return states[0]
