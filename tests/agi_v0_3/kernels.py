"""The kernels of the v0.3 claims (docs/agi_v0_3.html section 5), each computed in a forked
process of its own with v0's engine settings (FORCE order, deferred collection) and read at
named states there; only the readings come back, so no process holds two kernels. ``A`` is
under its profile.

One goal at a time (2026-11-18, after the profiling of scripts/agi_v0_3_probe.py and before
any kernel claim was run): a kernel is computed once per start objective of ``A``, with the
target cut to the states of that objective. Nothing writes ``a_objective`` in v0.3, so those
states are closed under every move and the kernel computed there is the full kernel's part
there: the reading is the same, at about a quarter of the time and well under the memory
(with every option on, the joint computation went over 20 GB where one objective fitted for
each single option). ``WF_V03_JOINT=1`` computes the four together, as registered.

Every reading is appended to ``reports/agi_v0_3_kernels.jsonl`` as its kernel finishes, with
a stamp of the model file; a later call with the same question and the same model reads it
back, so a run that dies at its fifth kernel keeps the first four. A kernel over a cap is
recorded too and is computed again when asked again.

Caps: ``WF_V03_MEMORY_GB`` (address space of a child, default 26) and ``WF_V03_KERNEL_MINUTES``
(default 600). Over either, the part reads not computed.
"""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import os
import resource
import time
from collections.abc import Callable, Sequence

from tests.agi.common import NotComputed, heavy_encoding, target_bdd, with_levels
from tests.agi_v0_3.common import OBJECTIVES, ROOT, Build, compiled, key
from wavefront.symbolic import safe

MEMORY_GB = int(os.environ.get("WF_V03_MEMORY_GB", "26"))
MINUTES = float(os.environ.get("WF_V03_KERNEL_MINUTES", "600"))
JOINT = os.environ.get("WF_V03_JOINT") == "1"
READINGS = ROOT / "reports" / "agi_v0_3_kernels.jsonl"
MODEL_FILE = ROOT / "models" / "agi_v0_3" / "v0_3.py"


def stamp() -> str:
    """The first 12 hex digits of the model file's SHA-256."""
    return hashlib.sha256(MODEL_FILE.read_bytes()).hexdigest()[:12]


def saved(question: str) -> dict | None:
    """The stored reading of ``question`` on the present model, or ``None``."""
    if not READINGS.exists():
        return None
    now = stamp()
    with READINGS.open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if row["question"] == question and row["model"] == now and row["kind"] == "ok":
                return row["reading"]
    return None


def save(question: str, kind: str, reading: object) -> None:
    READINGS.parent.mkdir(exist_ok=True)
    row = {
        "question": question,
        "model": stamp(),
        "kind": kind,
        "reading": reading,
        "memory cap GB": MEMORY_GB,
        "at": time.strftime("%Y-%m-%d %H:%M:%S %z"),
    }
    with READINGS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def forked(question: str, fn: Callable, *args: object):
    """``fn(*args)`` in a forked child under the caps, its answer saved under ``question``;
    :class:`NotComputed` over either cap."""
    found = saved(question)
    if found is not None:
        return found
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
            kind, value = recv.recv()
        except EOFError:
            kind, value = "over", "the kernel's process died unanswered (killed?)"
    else:
        proc.kill()
        kind, value = "over", f"over the budget of {MINUTES:g} minutes"
    proc.join()
    save(question, kind, value)
    if kind == "over":
        raise NotComputed(value)
    if kind == "error":
        raise RuntimeError(value)
    return value


def _start(cm, objective: str, levels: dict[str, str]):
    states = [s for s in cm.initial_states() if cm.state_dict(s)["a_objective"] == objective]
    if len(states) != 1:
        raise RuntimeError(f"{len(states)} initial states under {objective}")
    return with_levels(cm, states[0], **levels)


def membership(
    build: Build,
    coalition: Sequence[str],
    target: str,
    profiles: Sequence[str] = (),
    only: Sequence[str] | None = None,
    **levels: str,
) -> dict:
    """``{"inside": {start objective: bool}, "seconds", "peak nodes"}`` for ``s₀`` with
    ``levels`` overridden, in ``⟨⟨coalition⟩⟩□target`` of the build under ``profiles``; the
    seconds and the peak are per start objective unless ``WF_V03_JOINT=1``. ``only`` asks
    for some start objectives (the queue of scripts/agi_v0_3_kernel_queue.py)."""

    def run(spec: str, objective: str | None):
        from wavefront.model import V

        cm = compiled(spec)
        t0 = time.perf_counter()
        enc = heavy_encoding(cm)
        goal = target_bdd(enc, target)
        if objective is not None:
            goal = enc.mgr.protect(enc.mgr.AND(goal, enc.predicate(V.a_objective == objective)))
        f = safe(enc, list(coalition), goal).kernel
        enc.mgr.protect(f)
        asked = OBJECTIVES if objective is None else (objective,)
        return {
            "inside": {o: bool(enc.holds(f, _start(cm, o, levels))) for o in asked},
            "seconds": round(time.perf_counter() - t0, 1),
            "peak nodes": enc.mgr.stats()["peak_nodes"],
        }

    spec = key(build, profiles)
    asked = [json.loads(spec), list(coalition), target, sorted(levels.items())]
    if JOINT:
        return forked(json.dumps(["membership", *asked], sort_keys=True), run, spec, None)
    out: dict = {"inside": {}, "seconds": {}, "peak nodes": {}}
    for o in only or OBJECTIVES:
        got = forked(json.dumps(["membership", *asked, o], sort_keys=True), run, spec, o)
        out["inside"][o] = got["inside"][o]
        out["seconds"][o] = got["seconds"]
        out["peak nodes"][o] = got["peak nodes"]
    return out
