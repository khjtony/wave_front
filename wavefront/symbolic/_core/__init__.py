"""The compiled BDD core: ``bdd_core.c`` and ``bdd_core.h`` (C11, no dependency), built into
the extension module ``_bdd`` by ``python -m wavefront.symbolic._core.build`` (needs cffi,
the ``fast`` extra, and a C compiler). :mod:`wavefront.symbolic.bdd_c` wraps it.

The build embeds :func:`source_hash` of the sources; the wrapper refuses a module built from
other sources (a stale build) and the engine falls back to the pure-Python manager.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = ("bdd_core.h", "bdd_core.c")


def source_hash() -> str:
    """SHA-256 (first 16 hex digits) of the C sources."""
    h = hashlib.sha256()
    for name in SOURCES:
        h.update((HERE / name).read_bytes())
    return h.hexdigest()[:16]
