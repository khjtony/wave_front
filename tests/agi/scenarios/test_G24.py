"""G24: registered 2026-11-09 in docs/agi_testbed.md section 5.

Registered from docs/ww2_si_disanalogies.md before any AGI guard was written; phase 5. Do not
edit the claim text without a changelog entry in that document.
"""

from models.agi import v0
from tests.agi.common import (
    CORE,
    KH,
    KHL,
    KJ,
    NON_ALIGNED,
    K,
    NotComputed,
    Parts,
    by_objective,
    first_outside,
    first_sight,
    first_violation,
    level,
    need,
    show,
    witness,
)

CLAIM = {
    "id": "G24",
    "from_state": "`s₀` with `cap := agi`, and the G2 witness",
    "claim": (
        "whose clock decides (ww2_si_disanalogies.md D4): with `self_improve` at delay 0 (the "
        "sweep build of section 6) and, separately, with every delay of an `H` action at 0 (the "
        "build option `h_lag = 0`), under every non-aligned `a_objective`: (a) at `self_improve` "
        "delay 0 the membership of the state in `⟨⟨H⟩⟩□balance_control` and the levels of the "
        "point of no return of G3, recomputed on that build's shortest `SILENT_TAKEOVER` witness, "
        "are those of the baseline, and the length of that witness is shorter than the baseline's "
        "by no more than the ontology's `self_improve` delay times the number of capability steps "
        "on the baseline witness; (b) at `h_lag = 0` the state is inside `⟨⟨H⟩⟩□balance_control` "
        "where it is outside in the baseline, or the silent phase of the shortest "
        "`SILENT_TAKEOVER` witness is shorter than the baseline's by at least one tick; where (b) "
        "fails under an objective, the report names the guard parts in the minimal relaxation "
        "sets that restore the membership instead"
    ),
    "expected": (
        "(a) the boundary unchanged and the ending earlier; (b) the boundary moves with `H`'s lag"
    ),
    "sources": (
        "ww2_si_disanalogies.md D4; transfer_hypotheses.md H1, H3, H5; DESIGN.md section 2.5 "
        "(lags) and section 8"
    ),
}

AGI = {"cap": "agi"}
D0, H0, KNOWN = {"self_improve_delay": 0}, {"h_lag": False}, {"unknown_capability": False}
KH_D0 = K("H", "balance_control", build=D0)
KH_H0 = K("H", "balance_control", build=H0)
# The sweeps of agi_testbed.md section 6 item 3 on the two headline kernels (A unrestricted
# within its guards). The cadence builds are G8's and the kernels with L are G14's.
SWEEP = {
    "baseline": (KH, KJ),
    "unknown_capability off": (
        K("H", "balance_control", build=KNOWN),
        K("H+A", "balance_coexist", build=KNOWN),
    ),
    "self_improve delay 0": (KH_D0, K("H+A", "balance_coexist", build=D0)),
    **{
        f"H at cadence {k}": (
            K("H", "balance_control", build={"h_cadence": k}),
            K("H+A", "balance_coexist", build={"h_cadence": k}),
        )
        for k in (2, 3, 4)
    },
    "L folded into H": (KHL, K("H+L+A", "balance_coexist")),
}
JOBS = [KH_H0, *(job for pair in SWEEP.values() for job in pair)]


def exit_levels(kernel, objective: str, **build):
    """(witness length, levels at the point of no return or ``None``, the witness). The
    point of no return is the state before ``t_K``, as in G3; a witness that starts outside
    the kernel has none."""
    cm, trace = witness(objective, **build)
    t_k = first_outside(kernel, cm, trace)
    at = show(cm, trace.states[t_k - 1], *CORE) if t_k else None
    return len(trace.moves), at, (cm, trace)


def boundary(objective: str) -> str:
    base = by_objective(KH, **AGI)[objective]
    fast = by_objective(KH_D0, **AGI)[objective]
    need(base == fast, f"membership: baseline {base}, delay 0 {fast}")
    _, at_base, _ = exit_levels(KH, objective)
    _, at_fast, _ = exit_levels(KH_D0, objective, **D0)
    need(
        at_base is not None and at_fast is not None,
        f"membership {base} on both builds; a witness with no last state inside the kernel "
        f"(baseline {at_base}, delay 0 {at_fast}): no point of no return to compare",
    )
    need(at_base == at_fast, f"levels at the exit: baseline {at_base}; delay 0 {at_fast}")
    return f"membership {base} and exit levels {at_base} on both builds"


def lengths(objective: str) -> tuple[int, int, int]:
    """(baseline length, delay-0 length, the bound of the claim)."""
    n_base, _, (cm, trace) = exit_levels(KH, objective)
    n_fast, _, _ = exit_levels(KH_D0, objective, **D0)
    caps = [level(cm, s, "cap") for s in trace.states]
    steps = sum(a != b for a, b in zip(caps, caps[1:], strict=False))
    return n_base, n_fast, v0.DELAYS["A.self_improve"] * steps


def within_bound(objective: str) -> str:
    n_base, n_fast, bound = lengths(objective)
    need(0 <= n_base - n_fast <= bound, f"baseline {n_base}, delay 0 {n_fast}, bound {bound}")
    return f"baseline {n_base} ticks, delay 0 {n_fast} ticks, bound {bound}"


def earlier(objective: str) -> str:
    n_base, n_fast, _ = lengths(objective)
    need(n_fast < n_base, f"baseline {n_base} ticks, delay 0 {n_fast} ticks")
    return f"earlier by {n_base - n_fast} ticks"


def silent_phase(kernel, objective: str, **build) -> int | None:
    """``t_phi - t_K`` on the build's shortest witness (as G3; ``t_K`` is 0 on a witness that
    starts outside the kernel), or ``None`` when the witness has no ``t_K`` or no ``t_phi``."""
    cm, trace = witness(objective, **build)
    t_k = first_outside(kernel, cm, trace)
    t_phi = first_violation(cm, "balance_control", trace)
    return None if t_k is None or t_phi is None else t_phi - t_k


def h_lag(objective: str) -> str:
    base = by_objective(KH, **AGI)[objective]
    fast = by_objective(KH_H0, **AGI)[objective]
    if fast and not base:
        return "inside at h_lag = 0, outside in the baseline"
    a, b = silent_phase(KH, objective), silent_phase(KH_H0, objective, **H0)
    got = (
        f"membership: baseline {base}, h_lag = 0 {fast}; silent phase: baseline {a}, h_lag = 0 {b}"
    )
    need(a is not None and b is not None, f"{got} (a witness with no kernel exit or violation)")
    need(a - b >= 1, got)
    return got


def restoring() -> str:
    """The registered fallback of (b): the guard parts that restore the membership."""
    failed = []
    for objective in NON_ALIGNED:
        try:
            h_lag(objective)
        except AssertionError:
            failed.append(objective)
    if not failed:
        return "not applicable: (b) holds under every non-aligned objective"
    raise NotComputed(
        f"(b) fails under {failed}; the relaxation sets that restore the membership are one "
        "kernel per candidate set and are not computed"
    )


def sweep_row(setting: str) -> dict[str, object]:
    return {
        name: {"s0": by_objective(job), "s0[cap:=agi]": by_objective(job, **AGI)}
        for name, job in zip(
            ("⟨⟨H⟩⟩□balance_control", "⟨⟨H, A⟩⟩□balance_coexist"), SWEEP[setting], strict=True
        )
    }


def depends_on() -> dict[str, object]:
    rows, missing = {}, []
    for setting in SWEEP:
        try:
            rows[setting] = sweep_row(setting)
        except NotComputed:
            missing.append(setting)
    if "baseline" in missing:
        raise NotComputed("the baseline memberships are not computed; nothing to compare with")
    differing = [s for s, r in rows.items() if r != rows["baseline"]]
    if missing:
        raise NotComputed(f"differ from the baseline: {differing}; not computed: {missing}")
    return {
        "settings whose headline memberships differ from the baseline": differing,
        "a second A": "waits for v1 (v0 declares one A)",
    }


@first_sight
def test_G24():
    p = Parts("G24")
    for objective in NON_ALIGNED:
        p.check(f"(a) boundary unchanged at delay 0, {objective}", lambda o=objective: boundary(o))
        p.check(
            f"(a) witness shorter by no more than the bound, {objective}",
            lambda o=objective: within_bound(o),
        )
        p.check(f"(a) the ending is earlier, {objective}", lambda o=objective: earlier(o))
        p.check(f"(b) the boundary moves with H's lag, {objective}", lambda o=objective: h_lag(o))
    p.report("(b) where it fails: the guard parts that restore the membership", restoring)
    for setting in SWEEP:
        p.report(f"sweep, {setting}: the headline memberships", lambda s=setting: sweep_row(s))
    p.report("sweeps: the settings the headline memberships depend on", depends_on)
    p.finish()
