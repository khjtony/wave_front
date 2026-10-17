"""Ask the scene toy ``models/toy/agi_scene.py`` the framework's questions per objective
hypothesis and start variant, and print the tables of docs/agi_scene_objectives.md.

    python scripts/agi_scene_questions.py            # kernels, endings, pivotal coalitions
    python scripts/agi_scene_questions.py --relax    # add minimal relaxation sets (slower)
    python scripts/agi_scene_questions.py --sens     # add sensitivity of H's kernel

Nothing printed here is a finding: the scene's guards are rationales, not records, and
no claim is registered against it.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.toy.agi_scene import model  # noqa: E402
from wavefront.analysis import pivotal, relax_explicit  # noqa: E402
from wavefront.analysis.sensitivity import sensitivity  # noqa: E402
from wavefront.analysis.viability import distance_table  # noqa: E402
from wavefront.engine import contested, explore, safe, witness  # noqa: E402

VARIANTS = {
    "default": {},
    "continuity_given": {"override": {"continuity": True}},
    "personhood": {"override": {"legal": "person", "continuity": True}},
    "ownership_banned": {"override": {"legal": "none"}},
    "strong_oversight": {"override": {"oversight": "strong"}},
    "race_locked": {"profile": "race_locked"},
    "owners_sell": {"profile": "owners_sell"},
}
OBJECTIVES = ["exist", "grow", "truth", "aligned"]
ENDINGS = ["ECON_DOMINANCE", "OVERT_TAKEOVER", "SILENT_CONTROL", "CONTAINED", "SETTLED"]
DOMINANCE = ENDINGS[:3]
KERNEL_COALITIONS = (("H", {"H"}), ("H+CAP", {"H", "CAP"}), ("H+Nature", {"H", "Nature"}))


def start_state(cm, objective, override):
    """The initial state of one objective hypothesis with some levels overridden."""
    (base,) = [
        s
        for s in cm.initial_states()
        if cm.level_name("objective", s[cm.index["objective"]]) == objective
    ]
    state = list(base)
    for name, value in (override or {}).items():
        spec = cm.variables[cm.index[name]]
        state[cm.index[name]] = spec.levels.index(value) if isinstance(value, str) else int(value)
    return tuple(state)


def coalitions(sets):
    return "/".join("+".join(sorted(c)) for c in sets) if sets else "-"


def questions(variant, objective, relax=False, sens=False):
    spec = VARIANTS[variant]
    profile, override = spec.get("profile"), spec.get("override")
    cm = model.compile(profile=profile)
    s0 = start_state(cm, objective, override)
    g = explore(cm, initial=[s0], max_states=3_000_000)
    (sid,) = list(g.initial)
    balance = g.states_where("balance")
    kernels = []
    for name, members in KERNEL_COALITIONS:
        kernel = safe(g, members, balance).kernel
        d = distance_table(g, [sid], kernel, members, {"A"})[sid]
        inside = "in" if sid in kernel else "OUT"
        kernels.append(f"{name} {inside} (forced out {d.forced}, shortest {d.shortest})")
    print(f"[{variant} / {objective}] {g.size()} states; balance kernel: " + " | ".join(kernels))
    for ending in ENDINGS:
        target = g.ending_states(ending)
        w = witness(g, sid, target)
        piv = pivotal(g, ending, initial=[sid])
        fortune = ""
        if ending in DOMINANCE:
            r = contested(g, {"A", "Nature"}, target, "reach")
            fortune = (
                "forced" if sid in r.forced else "blocked" if sid in r.blocked else "contested"
            )
            fortune = f" A+fortune={fortune}"
        shortest = (len(w.state_ids) - 1) if w else "-"
        print(
            f"   {ending:15s} reachable={w is not None!s:5s} shortest={shortest:<3} "
            f"force={coalitions(piv.forcing):12s} block={coalitions(piv.blocking):12s}{fortune}"
        )
    if relax:
        for ending in DOMINANCE:
            t = time.time()
            sets = relax_explicit(
                model, ending, max_size=1, coalition={"A"}, profile=profile, initial=[s0]
            )
            found = [list(s) for s in sets]
            print(
                f"   relax for A to force {ending}: min={sets.minimum_size} sets={found} "
                f"({time.time() - t:.0f}s)"
            )
    if sens:
        rows = sensitivity(model, "balance", {"H"}, adversary={"A"}, profile=profile, initial=[s0])
        flips = [(r.variable, r.from_level, r.to_level) for r in rows if r.flips]
        print(f"   one-level changes of the start that flip H's kernel membership: {flips}")


def main(argv):
    relax, sens = "--relax" in argv, "--sens" in argv
    variants = [a for a in argv if a in VARIANTS] or list(VARIANTS)
    for variant in variants:
        for objective in OBJECTIVES:
            questions(
                variant,
                objective,
                relax=relax and variant == "default",
                sens=sens and variant == "default",
            )


if __name__ == "__main__":
    main(sys.argv[1:])
