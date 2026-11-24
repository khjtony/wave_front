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

__all__ = [
    "select",
    "capture_stderr",
    "why_died",
    "chosen",
    "attempts",
    "TABLE_FULL_STATUS",
    "TABLE_FULL_MESSAGE",
]

OWN = "c"
DEFAULT_THREADS = 12


def chosen(core: str, threads: str) -> tuple[str, int]:
    """The core and the worker threads of a kernel job from the two settings of its harness
    (``WF_V0x_CORE``, ``WF_V0x_THREADS``). Unset, the core is the multi-core one when its
    extension is built (2026-11-23: 2.2 times the own core on the success measure of
    docs/engine_multicore_design.md, with the same reading) and the own core otherwise;
    ``c`` asks for the own core. The threads default to 12, or to the machine's count if
    that is smaller; the own core has one."""
    from wavefront.symbolic import sylvan_available

    core = core.strip().lower() or ("sylvan" if sylvan_available() else OWN)
    if core != "sylvan":
        return core, 0
    return core, int(threads or 0) or min(DEFAULT_THREADS, os.cpu_count() or 1)


def attempts(core: str, threads: int) -> list[tuple[str, int]]:
    """The engines a kernel job tries, in order: the chosen one, and after a multi-core
    attempt that ran out of memory the own core on one thread, which needs about a quarter
    of the memory (owner's instruction of 2026-11-23)."""
    return [(core, threads), (OWN, 0)] if core == "sylvan" else [(core, threads)]


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
