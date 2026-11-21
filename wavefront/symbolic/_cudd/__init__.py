"""The CUDD binding (an engineering spike, docs/engine_reordering_spike.md): ``wf_cudd.c``
and ``wf_cudd.h``, a thin shim over CUDD's public interface, built into the extension module
``_cudd`` by ``python -m wavefront.symbolic._cudd.build`` against a CUDD source tree that
has been compiled (``--fetch`` downloads and compiles CUDD 3.0.0 under ``third_party/``).
:mod:`wavefront.symbolic.bdd_cudd` wraps it.

The build embeds :func:`source_hash` of the shim; the wrapper refuses a module built from
other sources.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = ("wf_cudd.h", "wf_cudd.c")


def source_hash() -> str:
    """SHA-256 (first 16 hex digits) of the shim's sources."""
    h = hashlib.sha256()
    for name in SOURCES:
        h.update((HERE / name).read_bytes())
    return h.hexdigest()[:16]
