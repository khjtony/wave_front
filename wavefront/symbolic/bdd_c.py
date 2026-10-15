"""The compiled BDD manager: the C core of :mod:`wavefront.symbolic._core` behind the
interface of the reference manager :class:`wavefront.symbolic.bdd.BDD`.

Every public method and attribute of the reference exists here with the same signature and
the same results: edges are the same kind of ``int`` (``(node << 1) | complement``, TRUE 0,
FALSE 1), and since both managers keep the same canonical form, an operation returns the
same function, ``node_count``, ``support``, ``pick_one`` and ``count`` the same values. Node
numbers may differ between the two managers (the free lists differ); compare functions
across managers with :meth:`BDD.transfer`.

Garbage collection has the reference's semantics: roots are the edges passed to
:meth:`BDD.gc`, protected edges and the ``bdd_roots()`` of registered holders (held weakly
here, in Python); the wrapper hands all of them to the C collector. :meth:`BDD.maybe_gc`
applies the same policy (``gc_min_nodes``, ``gc_factor``).

Importing this module raises :class:`ImportError` when the extension is not built
(``python -m wavefront.symbolic._core.build``) or was built from other sources. Use
:func:`wavefront.symbolic.manager` to pick a manager.
"""

from __future__ import annotations

import weakref
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager

from ._core import HERE, SOURCES, source_hash
from .bdd import FALSE, TRUE, VarSet

try:
    from ._core._bdd import ffi, lib
except ImportError as exc:  # not built
    raise ImportError(
        f"the compiled BDD core is not built ({exc}); run python -m wavefront.symbolic._core.build"
    ) from exc

if all((HERE / name).exists() for name in SOURCES):
    _built = ffi.string(lib.bdd_core_source_hash()).decode()
    if _built != source_hash():
        raise ImportError(
            f"the compiled BDD core is stale (built from sources {_built}, now "
            f"{source_hash()}); rerun python -m wavefront.symbolic._core.build"
        )

__all__ = ["BDD", "TRUE", "FALSE"]

_ERR = lib.BDD_ERR
_MISSING = lib.BDD_MISSING
_MAX_VARS = lib.BDD_MAX_VARS
_NSTATS = lib.BDD_NSTATS

_new = ffi.new
_from_buffer = ffi.from_buffer
_and = lib.bdd_and
_xor = lib.bdd_xor
_ite = lib.bdd_ite
_exists = lib.bdd_exists
_and_exists = lib.bdd_and_exists
_evaluate = lib.bdd_evaluate
_live = lib.bdd_live_nodes


def _u32(xs: Sequence[int]):
    return _new("uint32_t[]", xs) if xs else ffi.NULL


def _oom() -> MemoryError:
    return MemoryError("BDD node table exhausted (out of memory or 2**31 - 1 nodes)")


class BDD:
    """A BDD manager backed by the compiled core; the interface of
    :class:`wavefront.symbolic.bdd.BDD`."""

    TRUE = TRUE
    FALSE = FALSE
    core = "c"

    def __init__(self) -> None:
        m = lib.bdd_new()
        if m == ffi.NULL:
            raise _oom()
        self._m = ffi.gc(m, lib.bdd_delete)
        self.names: list[str] = []
        self._varsets: dict[tuple[int, ...], VarSet] = {}
        self._protected: dict[int, int] = {}
        self._holders: weakref.WeakSet = weakref.WeakSet()
        self.gc_min_nodes = 2_000_000
        self.gc_factor = 2.0
        self._after_gc = 0

    # -- variables -----------------------------------------------------------------------
    @property
    def num_vars(self) -> int:
        """Number of variables created."""
        return len(self.names)

    def add_var(self, name: str | None = None) -> int:
        """Create a variable at the bottom of the order; return its level."""
        level = len(self.names)
        if level >= _MAX_VARS or lib.bdd_add_var(self._m) != level:
            raise ValueError("too many BDD variables")
        self.names.append(name if name is not None else f"x{level}")
        return level

    def var(self, level: int) -> int:
        """The function that is true when variable ``level`` is 1."""
        self._check_level(level)
        return self._r(lib.bdd_mk(self._m, level, FALSE, TRUE))

    def nvar(self, level: int) -> int:
        """The function that is true when variable ``level`` is 0."""
        return self.var(level) ^ 1

    def _check_level(self, level: int) -> None:
        if not 0 <= level < len(self.names):
            raise ValueError(f"no BDD variable at level {level}")

    @staticmethod
    def _r(r: int) -> int:
        if r == _ERR:
            raise _oom()
        return r

    def varset(self, levels: Iterable[int]) -> VarSet:
        """The (cached) :class:`~wavefront.symbolic.bdd.VarSet` of ``levels``."""
        key = tuple(sorted(set(levels)))
        vs = self._varsets.get(key)
        if vs is None:
            mask = bytearray(len(self.names) + 1)
            for v in key:
                self._check_level(v)
                mask[v] = 1
            sid = lib.bdd_varset(self._m, _u32(key), len(key))
            if sid < 0:
                raise _oom()
            vs = VarSet(sid, key, mask, key[-1] if key else -1)
            self._varsets[key] = vs
        return vs

    def _as_varset(self, vs: VarSet | Iterable[int]) -> VarSet:
        if isinstance(vs, VarSet):
            # a VarSet of another manager names another id: resolve it by its levels
            return vs if self._varsets.get(vs.levels) is vs else self.varset(vs.levels)
        return self.varset(vs)

    # -- node inspection -----------------------------------------------------------------
    def top(self, f: int) -> int:
        """The level of the top variable of ``f`` (a large number for constants)."""
        return lib.bdd_top(self._m, f)

    def low(self, f: int) -> int:
        """The 0-cofactor of ``f`` with respect to its top variable."""
        return lib.bdd_low(self._m, f)

    def high(self, f: int) -> int:
        """The 1-cofactor of ``f`` with respect to its top variable."""
        return lib.bdd_high(self._m, f)

    @property
    def live_nodes(self) -> int:
        """Nodes currently allocated (including garbage not yet collected)."""
        return _live(self._m)

    @property
    def peak_nodes(self) -> int:
        """High-water mark of the node table (it never shrinks: collection does not move
        nodes)."""
        return lib.bdd_table_nodes(self._m)

    @property
    def gc_runs(self) -> int:
        """Collections run."""
        return self._raw_stats()[8]

    # -- boolean operations --------------------------------------------------------------
    def NOT(self, f: int) -> int:
        """Negation."""
        return f ^ 1

    def AND(self, f: int, g: int) -> int:
        """Conjunction."""
        r = _and(self._m, f, g)
        if r == _ERR:
            raise _oom()
        return r

    def OR(self, f: int, g: int) -> int:
        """Disjunction."""
        r = _and(self._m, f ^ 1, g ^ 1)
        if r == _ERR:
            raise _oom()
        return r ^ 1

    def XOR(self, f: int, g: int) -> int:
        """Exclusive or."""
        r = _xor(self._m, f, g)
        if r == _ERR:
            raise _oom()
        return r

    def IFF(self, f: int, g: int) -> int:
        """Equivalence."""
        return self.XOR(f, g) ^ 1

    def IMPLIES(self, f: int, g: int) -> int:
        """Implication."""
        return self.AND(f, g ^ 1) ^ 1

    def DIFF(self, f: int, g: int) -> int:
        """``f & ~g``."""
        return self.AND(f, g ^ 1)

    def ITE(self, f: int, g: int, h: int) -> int:
        """If-then-else."""
        r = _ite(self._m, f, g, h)
        if r == _ERR:
            raise _oom()
        return r

    def and_all(self, fs: Iterable[int]) -> int:
        """Conjunction of several functions (balanced)."""
        items = list(fs)
        if not items:
            return TRUE
        if len(items) == 1:
            return items[0]
        return self._r(lib.bdd_and_all(self._m, _u32(items), len(items)))

    def or_all(self, fs: Iterable[int]) -> int:
        """Disjunction of several functions (balanced)."""
        return self.and_all(f ^ 1 for f in fs) ^ 1

    def cube(self, assignment: Mapping[int, int | bool]) -> int:
        """The conjunction of literals ``level == value``."""
        levels = sorted(assignment, reverse=True)
        for v in levels:
            self._check_level(v)
        vals = bytes(1 if assignment[v] else 0 for v in levels)
        return self._r(
            lib.bdd_cube(self._m, _u32(levels), _from_buffer("uint8_t[]", vals), len(levels))
        )

    # -- quantification ------------------------------------------------------------------
    def exists(self, f: int, vs: VarSet | Iterable[int]) -> int:
        """``exists vs. f``."""
        vs = self._as_varset(vs)
        r = _exists(self._m, f, vs.id)
        if r == _ERR:
            raise _oom()
        return r

    def forall(self, f: int, vs: VarSet | Iterable[int]) -> int:
        """``forall vs. f``."""
        return self.exists(f ^ 1, vs) ^ 1

    def and_exists(self, f: int, g: int, vs: VarSet | Iterable[int]) -> int:
        """``exists vs. (f & g)`` without building ``f & g`` (relational product)."""
        vs = self._as_varset(vs)
        r = _and_exists(self._m, f, g, vs.id)
        if r == _ERR:
            raise _oom()
        return r

    # -- substitution --------------------------------------------------------------------
    def restrict(self, f: int, assignment: Mapping[int, int | bool]) -> int:
        """The cofactor of ``f`` by a partial assignment ``{level: value}``."""
        if not assignment:
            return f
        levels = list(assignment)
        vals = bytes(1 if assignment[v] else 0 for v in levels)
        return self._r(
            lib.bdd_restrict(self._m, f, _u32(levels), _from_buffer("uint8_t[]", vals), len(levels))
        )

    def simplify(self, f: int, care: int) -> int:
        """A function that agrees with ``f`` wherever ``care`` holds, usually smaller (the
        Coudert-Madre *restrict* operator). ``care`` must not be FALSE."""
        if care == FALSE:
            raise ValueError("simplify needs a satisfiable care set")
        return self._r(lib.bdd_simplify(self._m, f, care))

    def compose(self, f: int, mapping: Mapping[int, int]) -> int:
        """Substitute, simultaneously, the function ``mapping[v]`` for each variable ``v``
        in ``f``."""
        if not mapping:
            return f
        levels = list(mapping)
        fns = [mapping[v] for v in levels]
        return self._r(lib.bdd_compose(self._m, f, _u32(levels), _u32(fns), len(levels)))

    def rename(self, f: int, mapping: Mapping[int, int]) -> int:
        """Replace variable ``v`` by variable ``mapping[v]``. Fast when the renaming keeps
        the relative order of the variables of ``f``; correct in any case."""
        if not mapping:
            return f
        for w in mapping.values():
            self._check_level(w)
        src = list(mapping)
        dst = [mapping[v] for v in src]
        return self._r(lib.bdd_rename(self._m, f, _u32(src), _u32(dst), len(src)))

    def transfer(self, f: int, other: object, mapping: Mapping[int, int] | None = None) -> int:
        """Copy ``f`` into the manager ``other`` (compiled or reference), sending level
        ``v`` to ``mapping[v]`` (default: the same level); the orders may differ."""
        if isinstance(other, BDD):
            n = len(self.names)
            if mapping is None:
                table = ffi.NULL
            else:
                table = _u32([mapping[v] if v in mapping else _ERR for v in range(n)] or [0])
            r = lib.bdd_transfer(self._m, other._m, f, table, n if mapping is not None else 0)
            if r == _MISSING:
                level = lib.bdd_error_level(self._m)
                if mapping is not None and level not in mapping:
                    raise KeyError(level)
                target = level if mapping is None else mapping[level]
                raise ValueError(f"no BDD variable at level {target}")
            return self._r(r)
        get = (lambda v: v) if mapping is None else mapping.__getitem__
        nodes = self._dump([f])
        memo: dict[int, int] = {0: TRUE}
        for n, v, lo, hi in sorted(nodes, key=lambda x: -x[1] if x[0] else -(1 << 31)):
            if n == 0:
                continue
            r0 = memo[lo >> 1] ^ (lo & 1)
            r1 = memo[hi >> 1] ^ (hi & 1)
            memo[n] = other.ITE(other.var(get(v)), r1, r0)
        return memo[f >> 1] ^ (f & 1)

    def _dump(self, roots: Sequence[int]) -> list[tuple[int, int, int, int]]:
        """The nodes reachable from ``roots`` as ``(node, var, lo, hi)``."""
        k = self.node_count(list(roots))
        bufs = [_new("uint32_t[]", max(k, 1)) for _ in range(4)]
        got = lib.bdd_dump(self._m, _u32(list(roots)), len(roots), *bufs, k)
        if got < 0:
            raise _oom()
        nodes, vars_, los, his = bufs
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
        r = _evaluate(self._m, f, _from_buffer("uint8_t[]", bits), len(bits))
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
        k = lib.bdd_pick_one(self._m, f, lv, bits, cap)
        for i in range(k):
            out[lv[i]] = bits[i]
        return out

    def support(self, f: int | Iterable[int]) -> set[int]:
        """Levels of the variables ``f`` (or any of several functions) depends on."""
        roots = [f] if isinstance(f, int) else list(f)
        n = len(self.names)
        out = bytearray(n)
        k = lib.bdd_support(self._m, _u32(roots), len(roots), _from_buffer("uint8_t[]", out), n)
        if k < 0:
            raise _oom()
        return {v for v, b in enumerate(out) if b}

    def node_count(self, f: int | Iterable[int]) -> int:
        """Distinct nodes (the constant included) reachable from ``f`` or several roots."""
        roots = [f] if isinstance(f, int) else list(f)
        k = lib.bdd_node_count(self._m, _u32(roots), len(roots))
        if k < 0:
            raise _oom()
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
        rc = lib.bdd_count(
            self._m, f, _new("int32_t[]", pos) if pos else ffi.NULL, n, total, out, limbs
        )
        if rc == 1:
            v = lib.bdd_error_level(self._m)
            raise ValueError(f"count: the function depends on level {v}, not in the set")
        if rc != 0:
            raise _oom()
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

    def gc(self, roots: Iterable[int] = ()) -> int:
        """Reclaim every node not reachable from ``roots``, protected edges and registered
        holders. Computed-table entries over reclaimed nodes are dropped (the others are
        kept). Returns the number of nodes freed."""
        edges = list(roots)
        edges.extend(n << 1 for n in self._protected)
        for holder in list(self._holders):
            edges.extend(holder.bdd_roots())
        freed = lib.bdd_gc(self._m, _u32(edges), len(edges))
        if freed < 0:
            raise _oom()
        return freed

    def maybe_gc(self, roots: Iterable[int] = ()) -> bool:
        """Run :meth:`gc` if the live nodes exceed both ``gc_min_nodes`` and ``gc_factor``
        times the live nodes left by the previous collection. Callers pass every edge they
        still need that is not protected or held by a registered holder."""
        if _live(self._m) <= max(self.gc_min_nodes, self.gc_factor * self._after_gc):
            return False
        self.gc(roots)
        self._after_gc = _live(self._m)
        return True

    def _raw_stats(self) -> list[int]:
        out = _new("uint64_t[]", _NSTATS)
        lib.bdd_stats(self._m, out)
        return list(out)

    def stats(self) -> dict[str, int]:
        """Counters: live nodes, node-table high-water mark, cache sizes, collections; and
        for the compiled core the other computed tables and the bytes allocated (node and
        unique tables, computed tables)."""
        s = self._raw_stats()
        return {
            "live_nodes": s[0],
            "peak_nodes": s[1],
            "unique": s[2],
            "and_cache": s[3],
            "ite_cache": s[5],
            "gc_runs": s[8],
            "vars": s[9],
            "xor_cache": s[4],
            "exists_cache": s[6],
            "and_exists_cache": s[7],
            "node_bytes": s[10],
            "cache_bytes": s[11],
        }
