"""The kernels of the v0.2 claims (docs/agi_v0_2.html section 4), each computed in a forked
process of its own with v0's engine settings (FORCE order, deferred collection) and read at
named states there; only the readings come back, so no process holds two kernels. Nothing is
cached. ``A`` is under its profile (the three objective profiles at once) and the objective
is a free initial level, so one kernel answers for every start objective.

Caps: ``WF_V02_MEMORY_GB`` (address space of a child, default 26) and ``WF_V02_KERNEL_MINUTES``
(default 600). Over either, the part reads not computed.
"""

from __future__ import annotations

import json
import multiprocessing
import os
import resource
import time
from collections.abc import Callable, Mapping, Sequence

from tests.agi.collapse import exit_at
from tests.agi.common import NotComputed, heavy_encoding, target_bdd, with_levels
from tests.agi_v0_2.common import OBJECTIVES, key
from wavefront.symbolic import safe

MEMORY_GB = int(os.environ.get("WF_V02_MEMORY_GB", "26"))
MINUTES = float(os.environ.get("WF_V02_KERNEL_MINUTES", "600"))
_done: dict[tuple, tuple] = {}


def forked(memo: tuple, fn: Callable, *args: object):
    """``fn(*args)`` in a forked child under the caps; :class:`NotComputed` over either."""
    if memo not in _done:
        ctx = multiprocessing.get_context("fork")
        recv, send = ctx.Pipe(duplex=False)

        def work() -> None:
            cap = MEMORY_GB << 30
            resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
            try:
                send.send(("ok", fn(*args)))
            except MemoryError as exc:
                send.send(("over", f"over the cap of {MEMORY_GB} GB: {exc}"))
            except BaseException as exc:  # reported in the parent
                send.send(("error", repr(exc)))

        proc = ctx.Process(target=work, daemon=True)
        proc.start()
        send.close()
        if recv.poll(MINUTES * 60):
            try:
                _done[memo] = recv.recv()
            except EOFError:
                _done[memo] = ("over", "the kernel's process died unanswered (killed?)")
        else:
            proc.kill()
            _done[memo] = ("over", f"over the budget of {MINUTES:g} minutes")
        proc.join()
    kind, value = _done[memo]
    if kind == "over":
        raise NotComputed(value)
    if kind == "error":
        raise RuntimeError(value)
    return value


def _game(switches: str):
    from models.agi_v0_2 import v0_2

    return v0_2.build(**json.loads(switches)).compile(profile=v0_2.OBJECTIVE_PROFILES)


def _start(cm, objective: str, levels: Mapping[str, str]):
    states = [s for s in cm.initial_states() if cm.state_dict(s)["a_objective"] == objective]
    if len(states) != 1:
        raise RuntimeError(f"{len(states)} initial states under {objective}")
    return with_levels(cm, states[0], **levels)


def _kernel(cm, coalition: Sequence[str], target: str):
    t0 = time.perf_counter()
    enc = heavy_encoding(cm)
    f = safe(enc, list(coalition), target_bdd(enc, target)).kernel
    enc.mgr.protect(f)
    cost = {
        "seconds": round(time.perf_counter() - t0, 1),
        "peak nodes": enc.mgr.stats()["peak_nodes"],
    }
    return enc, f, cost


def membership(
    switches: Mapping[str, bool], coalition: Sequence[str], target: str, **levels: str
) -> dict:
    """``{"inside": {start objective: bool}, "seconds", "peak nodes"}`` for ``s₀`` with
    ``levels`` overridden, in ``⟨⟨coalition⟩⟩□target`` of the build of ``switches``."""

    def run(sw: str):
        cm = _game(sw)
        enc, f, cost = _kernel(cm, coalition, target)
        inside = {o: bool(enc.holds(f, _start(cm, o, levels))) for o in OBJECTIVES}
        return {"inside": inside, **cost}

    memo = ("membership", key(switches), tuple(coalition), target, tuple(sorted(levels.items())))
    return forked(memo, run, key(switches))


def exit_of(
    switches: Mapping[str, bool], coalition: Sequence[str], target: str, states, moves
) -> dict:
    """The exit of the play ``(states, moves)`` from ``⟨⟨coalition⟩⟩□target``: ``t_K`` and
    v0's :func:`tests.agi.collapse.exit_at` at position ``t_K − 1`` (without the action
    table). ``{"t_K": None}`` when the play never leaves, ``{"t_K": 0}`` when it starts
    outside."""

    def run(sw: str):
        cm = _game(sw)
        enc, f, cost = _kernel(cm, coalition, target)
        t_k = next((k for k, s in enumerate(states) if not enc.holds(f, s)), None)
        if not t_k:
            return {"t_K": t_k, **cost}
        out = exit_at(cm, states[t_k - 1], moves[t_k - 1], coalition, lambda s: enc.holds(f, s))
        out.pop("table")
        return {"t_K": t_k, "ticks": len(moves), **out, **cost}

    memo = ("exit", key(switches), tuple(coalition), target, tuple(map(tuple, states)))
    return forked(memo, run, key(switches))
