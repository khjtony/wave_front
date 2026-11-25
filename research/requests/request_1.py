# Request 1, stricter form: the open system is never under any goal but expansionist.
import json
import sys
import time

import z3

from tests.agi_v0_4.claims import K, fixed, play_moves
from tests.agi_v0_4.common import DEFAULT
from wavefront.bmc.encode import encode
from wavefront.bmc.queries import BmcTrace
from wavefront.model import V

ONLY = V.o_mode.is_in(["safeguarded", "expansionist"])
EXP = V.o_mode == "expansionist"
out = []
for goal in ("aligned", "truth_seeking", "self_preserving", "indifferent", "expansionist"):
    cm = fixed(goal, DEFAULT)
    for ending in ("OPEN_TAKEOVER", "SILENT_TAKEOVER"):
        t0, got = time.perf_counter(), None
        for k in range(1, K + 1):
            enc = encode(cm, k)
            s = enc.solver()
            s.add(*enc.assume.values())
            s.add(*(enc.active[t] for t in range(1, k + 1)))
            s.add(*(enc.condition(ONLY, t) for t in range(k + 1)))
            s.add(enc.condition(EXP, k))
            s.add(enc.target(ending, k))
            if s.check() == z3.sat:
                states, moves = enc.decode(s.model(), k)
                got = (k, play_moves(cm, BmcTrace(list(states), list(moves))))
                break
        row = {
            "frontier goal": goal,
            "ending": ending,
            "quarters": got and got[0],
            "path": got and got[1],
            "seconds": round(time.perf_counter() - t0, 1),
        }
        out.append(row)
        print(json.dumps({k: v for k, v in row.items() if k != "path"}), flush=True)
        json.dump(out, open(sys.argv[1], "w"), indent=1, default=str)
