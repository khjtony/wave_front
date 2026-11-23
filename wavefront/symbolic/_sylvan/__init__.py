"""The Sylvan core: ``wf_sylvan.c`` and ``wf_sylvan.h``, a thin layer over the multi-core BDD
package Sylvan, built into the extension module ``_sylvan`` by
``python -m wavefront.symbolic._sylvan.build`` (needs cffi, a C compiler, cmake and git).
:mod:`wavefront.symbolic.bdd_sylvan` wraps it. See docs/engine_multicore.md and
docs/engine_multicore_spike.md.

The build embeds :func:`source_hash` of the two sources; the wrapper refuses a module built
from other sources.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = ("wf_sylvan.h", "wf_sylvan.c")
# How a process ends when the node table fills in mid-operation (WFS_TABLE_FULL_STATUS and
# the message of wf_sylvan.c); here so that a harness can read them without the extension.
TABLE_FULL_STATUS = 86
TABLE_FULL_MESSAGE = "wavefront: the Sylvan node table is full"


def source_hash() -> str:
    """SHA-256 (first 16 hex digits) of the C sources."""
    h = hashlib.sha256()
    for name in SOURCES:
        h.update((HERE / name).read_bytes())
    return h.hexdigest()[:16]
