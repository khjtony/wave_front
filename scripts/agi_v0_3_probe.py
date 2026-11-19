"""Timing probe for the kernels of AGI v0.3 (docs/agi_v0_3.html section 6).

Computes ``⟨⟨H⟩⟩□balance_control`` with ``A`` under its profile on a v0.3 build, with v0's
engine settings, and prints seconds, node counts and peaks only: never a membership, a status
or a trace. Builds: ``closed`` (no open system, the treaty delay kept), ``bare`` (the open
system with ``pressure``, ``hosting`` and ``open_adoption`` off), one of the three options on
top of ``bare``, or ``default``.

``--objective`` computes the kernel on one objective of ``A`` only: the target is cut to the
states with that objective. Nothing writes ``a_objective`` in v0.3, so those states are
closed under every move and the result is the full kernel's part there.

    PYTHONPATH=. python scripts/agi_v0_3_probe.py --build bare --memory-gb 20
"""

from __future__ import annotations

import argparse
import resource
import time

from models.agi_v0_3 import v0_3
from tests.agi.common import heavy_encoding
from tests.agi_v0_3.common import CLOSED, DEFAULT
from wavefront.model import V
from wavefront.symbolic import safe

OPTIONS = ("pressure", "hosting", "open_adoption")
BARE = {**DEFAULT, **dict.fromkeys(OPTIONS, False)}
BUILDS = {"closed": CLOSED, "bare": BARE, "default": DEFAULT}
BUILDS |= {o: {**BARE, o: True} for o in OPTIONS}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", choices=list(BUILDS), required=True)
    ap.add_argument("--objective", choices=v0_3.OBJECTIVES)
    ap.add_argument("--memory-gb", type=int, default=20)
    args = ap.parse_args()
    cap = args.memory_gb << 30
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
    cm = v0_3.build(**BUILDS[args.build]).compile(profile=v0_3.OBJECTIVE_PROFILES)
    enc = heavy_encoding(cm)
    target = enc.predicate("balance_control")
    if args.objective:
        target = enc.mgr.protect(
            enc.mgr.AND(target, enc.predicate(V.a_objective == args.objective))
        )
    t0 = time.perf_counter()

    def tell(st: dict) -> None:
        print(f"layer {st['tick']} {st['seconds']}s nodes {st['nodes']}", flush=True)

    safe(enc, ["H"], target, on_iteration=tell)
    st = enc.mgr.stats()
    print(
        f"done v0.3 build={args.build} objective={args.objective or 'all'} "
        f"⟨⟨H⟩⟩□balance_control: {time.perf_counter() - t0:.1f}s peak {st['peak_nodes']} "
        f"maxrss_kb {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}",
        flush=True,
    )


if __name__ == "__main__":
    main()
