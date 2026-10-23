"""The crisis sub-games of Cold War v0 (decisions D5) and the flattened game.

``flat(cm)`` attaches Berlin 1948 (``USSR.blockade``), Cuba 1962 (``USSR.deploy_cuba``) and
Able Archer 83 (``USA.able_archer``) to a compiled coarse model (framework spec section 14).
"""

from __future__ import annotations

from wavefront.engine import flatten
from wavefront.engine.multires import FlatModel
from wavefront.model.compile import CompiledModel

from . import able_archer_1983, berlin_1948, cuba_1962

SUBGAMES = {
    "berlin_1948": berlin_1948,
    "cuba_1962": cuba_1962,
    "able_archer_1983": able_archer_1983,
}


def crises(names=tuple(SUBGAMES)):
    return [SUBGAMES[n].crisis() for n in names]


def flat(cm: CompiledModel, names=tuple(SUBGAMES)) -> FlatModel:
    """The coarse game ``cm`` with the named crisis sub-games inlined."""
    return flatten(cm, crises(names))
