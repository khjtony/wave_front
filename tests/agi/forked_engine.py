"""The BDD core of a forked kernel job, and what a child that died unanswered means
(tests/agi_v0_3/kernels.py, tests/agi_v0_4/kernels.py; docs/engine_multicore.md).

The core is chosen in the child, after the fork and before its first manager, so a Sylvan
core starts its worker threads there (threads do not survive a fork). Its tables are sized
from the child's address-space cap (``wavefront.symbolic.bdd_sylvan.table_sizes``).

A Sylvan core whose node table fills in the middle of an operation cannot raise: it ends the
process with :data:`TABLE_FULL_STATUS` and a line that starts with
:data:`TABLE_FULL_MESSAGE`. The child's stderr goes to a file next to its progress file, so
the parent can tell that death from a kill; the file is copied to the parent's stderr.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from wavefront.symbolic._sylvan import TABLE_FULL_MESSAGE, TABLE_FULL_STATUS

__all__ = ["select", "capture_stderr", "why_died", "TABLE_FULL_STATUS", "TABLE_FULL_MESSAGE"]


def select(core: str, threads: int) -> None:
    """In the child: the core (``""``: the default) and its worker threads (0: the default)."""
    if core:
        os.environ["WAVEFRONT_BDD"] = core
    if threads:
        os.environ["WAVEFRONT_BDD_THREADS"] = str(threads)


def capture_stderr(path: Path) -> None:
    """In the child: send file descriptor 2 to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sys.stderr.flush()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    os.dup2(fd, 2)
    os.close(fd)


def why_died(exitcode: int | None, path: Path) -> str:
    """In the parent: the reading of a child that sent no answer, from its exit status and
    its stderr (which is copied to the parent's stderr and removed)."""
    text = ""
    if path.exists():
        text = path.read_text(encoding="utf-8", errors="replace")
        path.unlink()
        if text:
            sys.stderr.write(text)
    if exitcode == TABLE_FULL_STATUS and TABLE_FULL_MESSAGE in text:
        line = next(x for x in text.splitlines() if TABLE_FULL_MESSAGE in x)
        return f"the node table filled: {line.strip()}"
    return f"the kernel's process died unanswered (exit status {exitcode}; killed?)"
