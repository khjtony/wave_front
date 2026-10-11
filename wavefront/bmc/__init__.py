"""Bounded model checking with Z3 (spec section 6).

This subpackage is the only part of ``wavefront`` that imports ``z3`` (the optional
``bmc`` dependency); importing it without ``z3-solver`` installed raises ``ImportError``.
"""

from .encode import Encoding, encode
from .queries import BmcTrace, RelaxResult, reach, relax

__all__ = ["encode", "Encoding", "reach", "relax", "BmcTrace", "RelaxResult"]
