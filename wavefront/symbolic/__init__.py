"""The symbolic engine: BDDs, the binary encoding of a compiled model, and fixpoints.

Pure Python, no third-party dependency. :mod:`.bdd` is the BDD manager, :mod:`.encode`
the encoding of a :class:`~wavefront.model.compile.CompiledModel` (state, next-state and
action bits; availability; next-state functions), :mod:`.solve` the controllable
predecessor, attractor, safety kernel, contested region, forward reachability and witness
traces. See ``docs/engine_scaling.md`` for the decision record and the benchmark.
"""

from .bdd import BDD, FALSE, TRUE
from .encode import Encoding, encode
from .solve import (
    SymbolicAttractor,
    SymbolicContested,
    SymbolicReach,
    SymbolicSafe,
    attractor,
    contested,
    cpre,
    reachable,
    safe,
    shortest,
    witness,
)

__all__ = [
    "BDD",
    "TRUE",
    "FALSE",
    "Encoding",
    "encode",
    "cpre",
    "attractor",
    "safe",
    "contested",
    "reachable",
    "shortest",
    "witness",
    "SymbolicAttractor",
    "SymbolicSafe",
    "SymbolicContested",
    "SymbolicReach",
]
