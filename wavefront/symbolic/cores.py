"""Selection of the BDD core: the compiled manager (:mod:`.bdd_c`) or the pure-Python
reference (:mod:`.bdd`).

:func:`manager` returns a new manager. With no argument it follows the environment variable
``WAVEFRONT_BDD``: unset or ``"c"`` gives the compiled manager when its extension imports and
the reference otherwise; ``"python"`` gives the reference. An explicit ``manager("c")`` does
not fall back: it raises :class:`ImportError` when the extension is missing or stale. Both
cores give identical results (docs/framework_spec.md section 15); a manager's ``core``
attribute says which one it is, and the fixpoints' ``stats`` repeat it.
"""

from __future__ import annotations

import os
import warnings

from .bdd import BDD

__all__ = ["ENV", "manager", "c_available", "c_import_error"]

ENV = "WAVEFRONT_BDD"
_CORES = ("c", "python")
_error: ImportError | None = None
_checked = False
_warned = False


def _load() -> type | None:
    global _error, _checked
    try:
        from .bdd_c import BDD as CBDD
    except ImportError as exc:
        _error, _checked = exc, True
        return None
    _error, _checked = None, True
    return CBDD


def c_available() -> bool:
    """Does the compiled core import (built, and from the current sources)?"""
    return _load() is not None


def c_import_error() -> ImportError | None:
    """Why the compiled core does not import, if it does not."""
    if not _checked:
        _load()
    return _error


def manager(kind: str | None = None):
    """A new BDD manager: ``kind`` is ``"c"``, ``"python"`` or ``None`` (follow
    ``WAVEFRONT_BDD``, falling back to the reference when the compiled core does not
    import)."""
    explicit = kind is not None
    kind = kind if explicit else (os.environ.get(ENV) or "c").strip().lower()
    if kind not in _CORES:
        raise ValueError(f"unknown BDD core {kind!r} (expected one of {', '.join(_CORES)})")
    if kind == "python":
        return BDD()
    cls = _load()
    if cls is not None:
        return cls()
    if explicit:
        raise ImportError(f"the compiled BDD core is not available: {_error}") from _error
    _warn_if_stale()
    return BDD()


def _warn_if_stale() -> None:
    """Warn once when an extension exists but does not import (stale or broken); a
    missing build falls back silently."""
    global _warned
    from ._core import HERE

    if _warned or not any(HERE.glob("_bdd*")):
        return
    _warned = True
    warnings.warn(f"using the pure-Python BDD manager: {_error}", RuntimeWarning, stacklevel=3)
