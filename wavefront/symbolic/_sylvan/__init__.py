"""The Sylvan core: ``wf_sylvan.c`` and ``wf_sylvan.h``, a thin layer over the multi-core BDD
package Sylvan, built into the extension module ``_sylvan`` by
``python -m wavefront.symbolic._sylvan.build`` (needs cffi, a C compiler, cmake and git).
:mod:`wavefront.symbolic.bdd_sylvan` wraps it. See docs/engine_multicore_spike.md.

The build embeds :func:`source_hash` of the two sources; the wrapper refuses a module built
from other sources.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = ("wf_sylvan.h", "wf_sylvan.c")


def source_hash() -> str:
    """SHA-256 (first 16 hex digits) of the C sources."""
    h = hashlib.sha256()
    for name in SOURCES:
        h.update((HERE / name).read_bytes())
    return h.hexdigest()[:16]
