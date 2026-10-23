"""C11: Adding the PRC changes the pivotal coalition for `DETERRENCE_HOLDS`.

Registered 2026-10-11 in docs/coldwar_testbed.md section 5. Do not edit the claim text
without a changelog entry in that document.

Reading (docs/cw_v0_decisions.md, R C11): for each year 1969 to 1972, the hindsight state
per hypothesis, on the model and on the scripted build (``prc_principal=False``): the
inclusion-minimal coalitions of the principals other than the USSR whose kernel of
balance_cw contains the state. Holds iff in every year the family is {{USA}} on the scripted
build and {{USA, PRC}} on the model. The fortune variant (with Nature) is reported. Engine:
symbolic.
"""

from ..common import HYPS, Timer, fmt, hindsight, kernel, minimal_coalitions

CLAIM = {
    "id": "C11",
    "from_state": "1969 to 1972",
    "claim": (
        "adding the PRC as a principal changes the pivotal coalition for "
        "`DETERRENCE_HOLDS` against the USSR from {USA} to {USA, PRC}"
    ),
    "expected": "as stated",
    "sources": "Westad 2017; FRUS 1969 to 1972",
}

YEARS = range(1969, 1973)


def family(aims, year, universe, prc_principal, nature=False):
    s = hindsight(year, aims, prc_principal)
    extra = ("Nature",) if nature else ()

    def works(c):
        coalition = tuple(sorted((*c, *extra)))
        return kernel(aims, coalition, prc_principal=prc_principal).contains(s)

    return minimal_coalitions(universe, works)


def test_C11():
    timer = Timer()
    print("\n[C11] engine: symbolic kernels of balance_cw, model and scripted build")
    results = {}
    for aims in HYPS:
        ok = True
        for y in YEARS:
            model_fam = family(aims, y, ("USA", "PRC"), True)
            scripted = family(aims, y, ("USA",), False)
            model_f = family(aims, y, ("USA", "PRC"), True, nature=True)
            scripted_f = family(aims, y, ("USA",), False, nature=True)
            print(
                f"[C11]   aims_USSR={aims} {y}: scripted {fmt(scripted)} -> principal "
                f"{fmt(model_fam)} (with Nature: {fmt(scripted_f)} -> {fmt(model_f)})"
            )
            ok = (
                ok and scripted == [frozenset({"USA"})] and model_fam == [frozenset({"USA", "PRC"})]
            )
        results[aims] = ok
        print(f"[C11] aims_USSR={aims}: {ok} ({timer})")
    assert any(results.values()), results
