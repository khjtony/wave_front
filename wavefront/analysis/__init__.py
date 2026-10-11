"""The analysis layer (spec section 7): viability kernels, the point of no return and the
silent phase, distances, strategy uniformity, pivotal coalitions, brute-force assumption
mining, sensitivity, trace clusters, the parameter budget and informativeness, and the
:func:`run_all` orchestrator used by the report and the CLI.

Every function is pure over a :class:`~wavefront.engine.Graph` or a
:class:`~wavefront.model.Model`; only :func:`run_all` combines them.
"""

from .cluster import Cluster, cluster, signature
from .pivotal import PivotalResult, pivotal
from .relax import RelaxSets, informativeness, minimal_relaxation_size, relax_explicit
from .run import (
    Analysis,
    EndingEntry,
    KernelEntry,
    UniformityNote,
    budget,
    fingerprint,
    run_all,
)
from .sensitivity import SensitivityRow, sensitivity, sensitivity_table
from .uniform import UniformityResult, is_uniform, strategy_closure
from .viability import (
    Distance,
    SilentPhase,
    distance,
    distance_table,
    point_of_no_return,
    silent_phase,
    viability,
)

__all__ = [
    "viability",
    "point_of_no_return",
    "silent_phase",
    "SilentPhase",
    "distance",
    "distance_table",
    "Distance",
    "is_uniform",
    "strategy_closure",
    "UniformityResult",
    "pivotal",
    "PivotalResult",
    "relax_explicit",
    "RelaxSets",
    "minimal_relaxation_size",
    "informativeness",
    "sensitivity",
    "sensitivity_table",
    "SensitivityRow",
    "cluster",
    "signature",
    "Cluster",
    "budget",
    "fingerprint",
    "run_all",
    "Analysis",
    "KernelEntry",
    "EndingEntry",
    "UniformityNote",
]
