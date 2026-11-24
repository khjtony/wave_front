"""The symbolic engine: BDDs, the binary encoding of a compiled model, and fixpoints.

:mod:`.bdd` is the reference BDD manager, in pure Python with no third-party dependency;
:mod:`.bdd_c` the same interface over a compiled C core (``_core``, built with cffi),
:mod:`.bdd_sylvan` the same over the multi-core package Sylvan (``_sylvan``, a spike), and
:func:`manager` picks one (``WAVEFRONT_BDD``, see :mod:`.cores`). :mod:`.encode`
the encoding of a :class:`~wavefront.model.compile.CompiledModel` (state, next-state and
action bits; availability; next-state functions), :mod:`.solve` the controllable
predecessor, attractor, safety kernel, contested region, forward reachability and witness
traces; :mod:`.substitute` the substitution one node at a time behind ``step="split"``
(``docs/engine_split_step.md``). See ``docs/engine_scaling.md`` for the decision record and
the benchmark.
"""

from .bdd import BDD, FALSE, TRUE
from .cores import c_available, manager, sylvan_available
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
    "manager",
    "c_available",
    "sylvan_available",
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
