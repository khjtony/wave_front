"""The multi-core BDD manager: Sylvan (work-stealing parallel BDD operations on a lock-free
node table) behind the interface of the reference manager
:class:`wavefront.symbolic.bdd.BDD`. An engineering spike: docs/engine_multicore_spike.md
says what it is for, what it measures and what is missing.

Edges are the same kind of ``int`` as in the other cores (``(node << 1) | complement``, TRUE
0, FALSE 1) and every operation returns the same function, so ``node_count``, ``support``,
``pick_one`` and ``count`` return the same values. Three things differ from the compiled core
:mod:`wavefront.symbolic.bdd_c`:

- **One node table per process.** Sylvan keeps one table, so every :class:`BDD` of this
  module is a view of it: variables are shared by level, and a collection asked for by one
  manager reclaims every node that no live manager protects, holds in a registered holder or
  was passed as a root of that call. Edges that another manager holds unprotected do not
  survive it. Keep one manager at a time, or protect what the others still need.
- **Fixed tables.** The node table and the operation cache are allocated once, when the
  first manager is made, with ``2 ** WAVEFRONT_SYLVAN_NODES_LOG2`` nodes (default 24; 24
  bytes each) and ``2 ** WAVEFRONT_SYLVAN_CACHE_LOG2`` cache entries (default 23; 36 bytes
  each). They do not grow. Sylvan's own collection is off, because the callers of this
  interface hold unprotected edges between the points where they call :meth:`BDD.maybe_gc`;
  when the node table fills up, Sylvan prints a message and ends the process (there is no
  :class:`MemoryError`). A collection empties the whole operation cache.
- **Threads.** ``WAVEFRONT_BDD_THREADS`` (default 1) worker threads are started with the
  first manager and stay for the life of the process; they sleep when idle. A process
  forked after that has no workers and must not make a manager.

``simplify`` returns a function that agrees with the reference's on the care set, not
necessarily the same function. ``peak_nodes`` is the largest number of live nodes seen at a
collection or a ``stats`` call.

Importing this module raises :class:`ImportError` when the extension is not built
(``python -m wavefront.symbolic._sylvan.build``) or was built from other sources.
"""

from __future__ import annotations

import gc as _pygc
import os
import weakref
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager

from ._sylvan import HERE, SOURCES, source_hash
from .bdd import FALSE, TRUE, VarSet

try:
    from ._sylvan._sylvan import ffi, lib
except ImportError as exc:  # not built
    raise ImportError(
        f"the Sylvan BDD core is not built ({exc}); run python -m wavefront.symbolic._sylvan.build"
    ) from exc

if all((HERE / name).exists() for name in SOURCES):
    _built = ffi.string(lib.wfs_source_hash()).decode()
    if _built != source_hash():
        raise ImportError(
            f"the Sylvan BDD core is stale (built from sources {_built}, now "
            f"{source_hash()}); rerun python -m wavefront.symbolic._sylvan.build"
        )

__all__ = ["BDD", "TRUE", "FALSE", "ENV_THREADS", "ENV_NODES", "ENV_CACHE"]

ENV_THREADS = "WAVEFRONT_BDD_THREADS"
ENV_NODES = "WAVEFRONT_SYLVAN_NODES_LOG2"
ENV_CACHE = "WAVEFRONT_SYLVAN_CACHE_LOG2"
_MAX_VARS = 32768
_NSTATS = lib.WFS_NSTATS

_new = ffi.new
_from_buffer = ffi.from_buffer
_and = lib.wfs_and
_xor = lib.wfs_xor
_ite = lib.wfs_ite
_exists = lib.wfs_exists
_and_exists = lib.wfs_and_exists
_evaluate = lib.wfs_evaluate
_live = lib.wfs_live_nodes

_pid: int | None = None
_table_nodes = 0
_peak = 0
_managers: weakref.WeakSet = weakref.WeakSet()


def _env_int(name: str, default: int, lo: int, hi: int) -> int:
    raw = os.environ.get(name)
    value = default if raw is None or not raw.strip() else int(raw)
    if not lo <= value <= hi:
        raise ValueError(f"{name}={value} is outside {lo}..{hi}")
    return value


def _start() -> None:
    """Start the workers and allocate the tables (once per process)."""
    global _pid, _table_nodes
    if _pid is not None:
        if _pid != os.getpid():
            raise RuntimeError(
                "the Sylvan core was started in the parent process and its worker threads "
                "did not survive the fork; make the first manager after forking"
            )
        return
    threads = _env_int(ENV_THREADS, 1, 1, 256)
    nodes = _env_int(ENV_NODES, 24, 16, 36)
    cache = _env_int(ENV_CACHE, 23, 16, 36)
    lib.wfs_init(threads, nodes, cache)
    _pid = os.getpid()
    _table_nodes = 1 << nodes


def _u32(xs: Sequence[int]):
    return _new("uint32_t[]", xs) if xs else ffi.NULL


def _u64(xs: Sequence[int]):
    return _new("uint64_t[]", xs) if xs else ffi.NULL


def _note_live() -> int:
    global _peak
    live = _live()
    if live > _peak:
        _peak = live
    return live


class BDD:
    """A BDD manager backed by Sylvan; the interface of :class:`wavefront.symbolic.bdd.BDD`.
    All managers of a process share one node table (see the module docstring)."""

    TRUE = TRUE
    FALSE = FALSE
    core = "sylvan"

    def __init__(self) -> None:
        _start()
        self.names: list[str] = []
        self._varsets: dict[tuple[int, ...], VarSet] = {}
        self._protected: dict[int, int] = {}
        self._holders: weakref.WeakSet = weakref.WeakSet()
        self.gc_min_nodes = 2_000_000
        self.gc_factor = 2.0
        self._after_gc = 0
        if _live() > _table_nodes // 4:
            # the table is shared: reclaim what dead managers left before starting
            _pygc.collect()
            if not _managers:
                self.gc()
        _managers.add(self)

    @property
    def workers(self) -> int:
        """Worker threads of the process-wide Sylvan instance."""
        return lib.wfs_workers()

    # -- variables -----------------------------------------------------------------------
    @property
    def num_vars(self) -> int:
        """Number of variables created."""
        return len(self.names)

    def add_var(self, name: str | None = None) -> int:
        """Create a variable at the bottom of the order; return its level."""
        level = len(self.names)
        if level >= _MAX_VARS:
            raise ValueError("too many BDD variables")
        self.names.append(name if name is not None else f"x{level}")
        return level

    def var(self, level: int) -> int:
        """The function that is true when variable ``level`` is 1."""
        self._check_level(level)
        return lib.wfs_var(level)

    def nvar(self, level: int) -> int:
        """The function that is true when variable ``level`` is 0."""
        return self.var(level) ^ 1

    def _check_level(self, level: int) -> None:
        if not 0 <= level < len(self.names):
            raise ValueError(f"no BDD variable at level {level}")

    def varset(self, levels: Iterable[int]) -> VarSet:
        """The (cached) :class:`~wavefront.symbolic.bdd.VarSet` of ``levels``; its ``id`` is
        the edge of the positive cube Sylvan quantifies over."""
        key = tuple(sorted(set(levels)))
        vs = self._varsets.get(key)
        if vs is None:
            mask = bytearray(len(self.names) + 1)
            for v in key:
                self._check_level(v)
                mask[v] = 1
            vs = VarSet(lib.wfs_varset(_u32(key), len(key)), key, mask, key[-1] if key else -1)
            self._varsets[key] = vs
        return vs

    def _as_varset(self, vs: VarSet | Iterable[int]) -> VarSet:
        if isinstance(vs, VarSet):
            return vs if self._varsets.get(vs.levels) is vs else self.varset(vs.levels)
        return self.varset(vs)

    # -- node inspection -----------------------------------------------------------------
    def top(self, f: int) -> int:
        """The level of the top variable of ``f`` (a large number for constants)."""
        return lib.wfs_top(f)

    def low(self, f: int) -> int:
        """The 0-cofactor of ``f`` with respect to its top variable."""
        return lib.wfs_low(f)

    def high(self, f: int) -> int:
        """The 1-cofactor of ``f`` with respect to its top variable."""
        return lib.wfs_high(f)

    @property
    def live_nodes(self) -> int:
        """Nodes in the process-wide table (including garbage not yet collected, and the
        nodes of the other managers)."""
        return _note_live()

    @property
    def peak_nodes(self) -> int:
        """The largest number of live nodes seen at a collection or a ``stats`` call."""
        _note_live()
        return _peak

    @property
    def gc_runs(self) -> int:
        """Collections run (in the process)."""
        return self._raw_stats()[3]

    # -- boolean operations --------------------------------------------------------------
    def NOT(self, f: int) -> int:
        """Negation."""
        return f ^ 1

    def AND(self, f: int, g: int) -> int:
        """Conjunction."""
        return _and(f, g)

    def OR(self, f: int, g: int) -> int:
        """Disjunction."""
        return _and(f ^ 1, g ^ 1) ^ 1

    def XOR(self, f: int, g: int) -> int:
        """Exclusive or."""
        return _xor(f, g)

    def IFF(self, f: int, g: int) -> int:
        """Equivalence."""
        return _xor(f, g) ^ 1

    def IMPLIES(self, f: int, g: int) -> int:
        """Implication."""
        return _and(f, g ^ 1) ^ 1

    def DIFF(self, f: int, g: int) -> int:
        """``f & ~g``."""
        return _and(f, g ^ 1)

    def ITE(self, f: int, g: int, h: int) -> int:
        """If-then-else."""
        return _ite(f, g, h)

    def and_all(self, fs: Iterable[int]) -> int:
        """Conjunction of several functions (balanced)."""
        items = list(fs)
        if not items:
            return TRUE
        if len(items) == 1:
            return items[0]
        return lib.wfs_and_all(_u64(items), len(items))

    def or_all(self, fs: Iterable[int]) -> int:
        """Disjunction of several functions (balanced)."""
        return self.and_all(f ^ 1 for f in fs) ^ 1

    def cube(self, assignment: Mapping[int, int | bool]) -> int:
        """The conjunction of literals ``level == value``."""
        levels = sorted(assignment, reverse=True)
        for v in levels:
            self._check_level(v)
        vals = bytes(1 if assignment[v] else 0 for v in levels)
        return lib.wfs_cube(_u32(levels), _from_buffer("uint8_t[]", vals), len(levels))

    # -- quantification ------------------------------------------------------------------
    def exists(self, f: int, vs: VarSet | Iterable[int]) -> int:
        """``exists vs. f``."""
        return _exists(f, self._as_varset(vs).id)

    def forall(self, f: int, vs: VarSet | Iterable[int]) -> int:
        """``forall vs. f``."""
        return _exists(f ^ 1, self._as_varset(vs).id) ^ 1

    def and_exists(self, f: int, g: int, vs: VarSet | Iterable[int]) -> int:
        """``exists vs. (f & g)`` without building ``f & g`` (relational product)."""
        return _and_exists(f, g, self._as_varset(vs).id)

    # -- substitution --------------------------------------------------------------------
    def restrict(self, f: int, assignment: Mapping[int, int | bool]) -> int:
        """The cofactor of ``f`` by a partial assignment ``{level: value}``."""
        if not assignment:
            return f
        levels = sorted(assignment, reverse=True)
        vals = bytes(1 if assignment[v] else 0 for v in levels)
        return lib.wfs_restrict(f, _u32(levels), _from_buffer("uint8_t[]", vals), len(levels))

    def simplify(self, f: int, care: int) -> int:
        """A function that agrees with ``f`` wherever ``care`` holds, usually smaller
        (Sylvan's *restrict*). ``care`` must not be FALSE."""
        if care == FALSE:
            raise ValueError("simplify needs a satisfiable care set")
        return lib.wfs_simplify(f, care)

    def compose(self, f: int, mapping: Mapping[int, int]) -> int:
        """Substitute, simultaneously, the function ``mapping[v]`` for each variable ``v``
        in ``f``."""
        if not mapping:
            return f
        levels = list(mapping)
        fns = [mapping[v] for v in levels]
        return lib.wfs_compose(f, _u32(levels), _u64(fns), len(levels))

    def rename(self, f: int, mapping: Mapping[int, int]) -> int:
        """Replace variable ``v`` by variable ``mapping[v]`` (a composition with
        variables)."""
        if not mapping:
            return f
        return self.compose(f, {v: self.var(w) for v, w in mapping.items()})

    def transfer(self, f: int, other: object, mapping: Mapping[int, int] | None = None) -> int:
        """Copy ``f`` into the manager ``other`` (of any core), sending level ``v`` to
        ``mapping[v]`` (default: the same level); the orders may differ. Node by node in
        Python: meant for checks, not for large functions."""
        if isinstance(other, BDD) and mapping is None:
            for v in self.support(f):
                other._check_level(v)
            return f
        get = (lambda v: v) if mapping is None else mapping.__getitem__
        memo: dict[int, int] = {0: TRUE}
        for n, v, lo, hi in sorted(self._dump([f]), key=lambda x: -x[1]):
            if n == 0:
                continue
            r0 = memo[lo >> 1] ^ (lo & 1)
            r1 = memo[hi >> 1] ^ (hi & 1)
            memo[n] = other.ITE(other.var(get(v)), r1, r0)
        return memo[f >> 1] ^ (f & 1)

    def _dump(self, roots: Sequence[int]) -> list[tuple[int, int, int, int]]:
        """The nodes reachable from ``roots`` as ``(node, var, lo, hi)``: ``lo`` and ``hi``
        are the cofactors of the edge ``node << 1``, and the constant is node 0."""
        k = self.node_count(list(roots))
        nodes, los, his = (_new("uint64_t[]", max(k, 1)) for _ in range(3))
        vars_ = _new("uint32_t[]", max(k, 1))
        got = lib.wfs_dump(_u64(list(roots)), len(roots), nodes, vars_, los, his, k)
        if got < 0:
            raise MemoryError("out of memory while walking a BDD")
        return [(nodes[i], vars_[i], los[i], his[i]) for i in range(got)]

    # -- queries -------------------------------------------------------------------------
    def evaluate(self, f: int, value: Mapping[int, int] | Sequence[int]) -> bool:
        """``f`` under a total assignment (a mapping or a sequence indexed by level; levels
        missing from a mapping read as 0)."""
        if isinstance(value, Mapping):
            n = len(self.names)
            bits = bytearray(n)
            for k, b in value.items():
                if 0 <= k < n and b:
                    bits[k] = 1
        else:
            try:
                bits = bytes(value)
            except (TypeError, ValueError):
                bits = bytes(1 if b else 0 for b in value)
        r = _evaluate(f, _from_buffer("uint8_t[]", bits), len(bits))
        if r < 0:
            raise IndexError("evaluate: the assignment is shorter than a level it needs")
        return r == 1

    def pick_one(self, f: int, levels: Iterable[int] = ()) -> dict[int, int] | None:
        """A satisfying assignment of ``f`` (``None`` if ``f`` is FALSE) as ``{level: bit}``
        covering the variables on the chosen path and every level in ``levels`` (0 where
        free). The 0 branch is preferred, so the result is the least in that order."""
        if f == FALSE:
            return None
        out = dict.fromkeys(levels, 0)
        cap = len(self.names) + 1
        lv = _new("uint32_t[]", cap)
        bits = _new("uint8_t[]", cap)
        k = lib.wfs_pick_one(f, lv, bits, cap)
        if k < 0:
            raise ValueError("pick_one: the function depends on a level of another manager")
        for i in range(k):
            out[lv[i]] = bits[i]
        return out

    def support(self, f: int | Iterable[int]) -> set[int]:
        """Levels of the variables ``f`` (or any of several functions) depends on."""
        roots = [f] if isinstance(f, int) else list(f)
        n = max(len(self.names), 1)
        out = bytearray(n)
        k = lib.wfs_support(_u64(roots), len(roots), _from_buffer("uint8_t[]", out), n)
        if k < 0:
            raise ValueError("support: the function depends on a level of another manager")
        return {v for v, b in enumerate(out) if b}

    def node_count(self, f: int | Iterable[int]) -> int:
        """Distinct nodes (the constant included) reachable from ``f`` or several roots."""
        roots = [f] if isinstance(f, int) else list(f)
        k = lib.wfs_node_count(_u64(roots), len(roots))
        if k < 0:
            raise MemoryError("out of memory while walking a BDD")
        return k

    def count(self, f: int, levels: Iterable[int]) -> int:
        """The number of assignments to ``levels`` satisfying ``f``. ``f`` must depend only
        on variables in ``levels``."""
        order = sorted(set(levels))
        n = len(self.names)
        pos = [-1] * n
        for i, v in enumerate(order):
            if 0 <= v < n:
                pos[v] = i
        total = len(order)
        limbs = total // 32 + 1
        out = _new("uint32_t[]", limbs)
        rc = lib.wfs_count(f, _new("int32_t[]", pos) if pos else ffi.NULL, n, total, out, limbs)
        if rc == 1:
            v = lib.wfs_error_level()
            raise ValueError(f"count: the function depends on level {v}, not in the set")
        if rc != 0:
            raise MemoryError("out of memory while counting")
        r = 0
        for i in reversed(range(limbs)):
            r = (r << 32) | out[i]
        return r

    # -- garbage collection --------------------------------------------------------------
    def protect(self, f: int) -> int:
        """Keep ``f`` alive across :meth:`gc` until :meth:`unprotect`; returns ``f``."""
        self._protected[f >> 1] = self._protected.get(f >> 1, 0) + 1
        return f

    def unprotect(self, f: int) -> None:
        """Release one :meth:`protect` of ``f``."""
        n = f >> 1
        k = self._protected.get(n, 0) - 1
        if k <= 0:
            self._protected.pop(n, None)
        else:
            self._protected[n] = k

    @contextmanager
    def protecting(self, *edges: int | None) -> Iterator[None]:
        """Protect ``edges`` (``None`` entries are skipped) for the duration of a block."""
        held = [e for e in edges if e is not None]
        for e in held:
            self.protect(e)
        try:
            yield
        finally:
            for e in held:
                self.unprotect(e)

    def register(self, holder: object) -> None:
        """Keep the edges returned by ``holder.bdd_roots()`` alive while ``holder`` lives."""
        self._holders.add(holder)

    def _roots(self) -> list[int]:
        edges = [n << 1 for n in self._protected]
        edges.extend(vs.id for vs in self._varsets.values())
        for holder in list(self._holders):
            edges.extend(holder.bdd_roots())
        return edges

    def gc(self, roots: Iterable[int] = ()) -> int:
        """Reclaim every node of the process-wide table not reachable from ``roots`` or from
        the protected edges, registered holders and varsets of any live manager. Empties the
        operation cache. Returns the number of nodes freed."""
        edges = list(roots)
        for mgr in list(_managers):
            edges.extend(mgr._roots())
        if self not in _managers:
            edges.extend(self._roots())
        _note_live()
        return lib.wfs_gc(_u64(edges), len(edges))

    def maybe_gc(self, roots: Iterable[int] = ()) -> bool:
        """Run :meth:`gc` if the live nodes exceed both ``gc_min_nodes`` and ``gc_factor``
        times the live nodes left by the previous collection. Callers pass every edge they
        still need that is not protected or held by a registered holder."""
        if _note_live() <= max(self.gc_min_nodes, self.gc_factor * self._after_gc):
            return False
        self.gc(roots)
        self._after_gc = _live()
        return True

    def _raw_stats(self) -> list[int]:
        out = _new("uint64_t[]", _NSTATS)
        lib.wfs_stats(out)
        return list(out)

    def stats(self) -> dict[str, int]:
        """Counters of the process-wide table: live nodes, their high-water mark,
        collections, the fixed sizes of the node table and the operation cache and their
        bytes, and the worker threads. The reference's per-operation cache sizes read 0:
        Sylvan has one cache for all operations and does not count its entries."""
        s = self._raw_stats()
        global _peak
        _peak = max(_peak, s[0])
        return {
            "live_nodes": s[0],
            "peak_nodes": _peak,
            "unique": s[0],
            "and_cache": 0,
            "ite_cache": 0,
            "gc_runs": s[3],
            "vars": len(self.names),
            "table_nodes": s[1],
            "cache_entries": s[2],
            "node_bytes": s[4],
            "cache_bytes": s[5],
            "workers": lib.wfs_workers(),
        }
