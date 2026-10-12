"""Loaders for the quantitative datasets behind the hindsight snapshots.

Each loader returns plain rows (one ``dict`` per record) with provenance attached to every
row: ``source`` (the dataset's citation), ``version`` and ``obtained_via`` (where this copy of
the file came from: the official host, a mirror, or a local file). The official CSV files and
the R data mirrors are both accepted. Reading an ``.rda`` file needs the optional ``data``
extra (``pyreadr``), which is imported only when such a file is read, so the core keeps no
third-party dependency.
"""

from . import mid, nmc

__all__ = ["mid", "nmc"]
