"""A reduced ordered binary decision diagram (BDD) manager in pure Python.

Representation
--------------
Nodes live in three parallel lists, ``var``, ``lo`` and ``hi``; node 0 is the constant
one. A function is an *edge*, an ``int`` ``(node << 1) | c`` where ``c`` is a complement
bit, so negation is ``edge ^ 1`` and costs nothing. :data:`TRUE` is ``0`` and
:data:`FALSE` is ``1``. Canonical form: the ``hi`` edge of a stored node is never
complemented, ``lo != hi``, and every ``(var, lo, hi)`` triple is stored once (the unique
table, a ``dict`` keyed by one packed ``int``). Two edges are equal as integers iff they
denote the same function.

Variables are identified with their *level*: variable ``k`` is the ``k``-th created, and
the order is fixed (no reordering). The encoder (:mod:`wavefront.symbolic.encode`) creates
variables in the order it wants.

Operations
----------
``AND``, ``OR``, ``XOR``, ``ITE`` (with computed tables), negation, ``exists`` / ``forall``
over variable sets, ``and_exists`` (relational product with early quantification),
``restrict`` (cofactor by a partial assignment), ``simplify`` (the Coudert-Madre restrict
operator: any function that agrees with ``f`` on a care set), ``compose`` (simultaneous
substitution of functions for variables), ``rename``, ``pick_one``, ``count``,
``node_count`` and ``evaluate``.

The recursive operations are closures over the node lists and caches; Python recursion
depth is bounded by a small multiple of the number of variables, and the manager raises the
interpreter's recursion limit accordingly.

Memory
------
Dead nodes are reclaimed by :meth:`BDD.gc`, a non-moving mark and sweep: edges held by the
caller stay valid if they are reachable from the roots passed to ``gc``, from edges
registered with :meth:`BDD.protect`, or from objects registered with :meth:`BDD.register`
(any object with a ``bdd_roots()`` method, held weakly). Computed tables are cleared by a
collection and when they grow past a limit between top-level operations.
"""

from __future__ import annotations

import sys
import weakref
from array import array
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

__all__ = ["BDD", "TRUE", "FALSE", "VarSet"]

TRUE = 0
FALSE = 1

_TERMVAR = 1 << 30  # the level of the constant node: below every variable
_ESHIFT = 35  # bits per edge in packed keys (edges < 2**35)
_VSHIFT = 15  # bits per level in packed unique-table keys (levels < 2**15)
_SSHIFT = 20  # bits per varset id in packed cache keys
_CACHE_LIMIT = 3_000_000
_RECURSION = 20_000  # enough for about 5,000 variables (see add_var)

if sys.getrecursionlimit() < _RECURSION:
    sys.setrecursionlimit(_RECURSION)


@dataclass(frozen=True, eq=False)
class VarSet:
    """A set of variables for quantification, with an id used in cache keys."""

    id: int
    levels: tuple[int, ...]
    mask: bytearray
    maxv: int


class BDD:
    """A BDD manager. See the module docstring for the representation."""

    TRUE = TRUE
    FALSE = FALSE

    def __init__(self) -> None:
        self._var = array("q", [_TERMVAR])
        self._lo = array("q", [0])
        self._hi = array("q", [0])
        self._unique: dict[int, int] = {}
        self._free: list[int] = []
        self.names: list[str] = []
        self._and_cache: dict[int, int] = {}
        self._xor_cache: dict[int, int] = {}
        self._ite_cache: dict[int, int] = {}
        self._ex_cache: dict[int, int] = {}
        self._ae_cache: dict[int, int] = {}
        self._varsets: dict[tuple[int, ...], VarSet] = {}
        self._protected: dict[int, int] = {}
        self._holders: weakref.WeakSet = weakref.WeakSet()
        self.peak_nodes = 1
        self.gc_runs = 0
        self._build()

    # -- variables -----------------------------------------------------------------------
    @property
    def num_vars(self) -> int:
        """Number of variables created."""
        return len(self.names)

    def add_var(self, name: str | None = None) -> int:
        """Create a variable at the bottom of the order; return its level."""
        level = len(self.names)
        if level >= 1 << _VSHIFT:
            raise ValueError("too many BDD variables")
        self.names.append(name if name is not None else f"x{level}")
        need = 4 * (level + 1) + 500
        if sys.getrecursionlimit() < need:
            sys.setrecursionlimit(need)
        return level

    def var(self, level: int) -> int:
        """The function that is true when variable ``level`` is 1."""
        self._check_level(level)
        return self._mk(level, FALSE, TRUE)

    def nvar(self, level: int) -> int:
        """The function that is true when variable ``level`` is 0."""
        return self.var(level) ^ 1

    def _check_level(self, level: int) -> None:
        if not 0 <= level < len(self.names):
            raise ValueError(f"no BDD variable at level {level}")

    def varset(self, levels: Iterable[int]) -> VarSet:
        """The (cached) :class:`VarSet` of ``levels``."""
        key = tuple(sorted(set(levels)))
        vs = self._varsets.get(key)
        if vs is None:
            mask = bytearray(len(self.names) + 1)
            for v in key:
                self._check_level(v)
                mask[v] = 1
            vs = VarSet(len(self._varsets), key, mask, key[-1] if key else -1)
            if vs.id >= 1 << _SSHIFT:
                raise ValueError("too many variable sets")
            self._varsets[key] = vs
        return vs

    # -- node inspection -----------------------------------------------------------------
    def top(self, f: int) -> int:
        """The level of the top variable of ``f`` (a large number for constants)."""
        return self._var[f >> 1]

    def low(self, f: int) -> int:
        """The 0-cofactor of ``f`` with respect to its top variable."""
        return self._lo[f >> 1] ^ (f & 1)

    def high(self, f: int) -> int:
        """The 1-cofactor of ``f`` with respect to its top variable."""
        return self._hi[f >> 1] ^ (f & 1)

    @property
    def live_nodes(self) -> int:
        """Nodes currently allocated (including garbage not yet collected)."""
        return len(self._var) - len(self._free)

    # -- core construction (closures over the node lists) -------------------------------
    def _build(self) -> None:
        var, lo, hi = self._var, self._lo, self._hi
        unique, free = self._unique, self._free
        and_cache, xor_cache, ite_cache = self._and_cache, self._xor_cache, self._ite_cache
        es, vsh = _ESHIFT, _VSHIFT

        def mk(v: int, low: int, high: int) -> int:
            if low == high:
                return low
            if high & 1:
                low ^= 1
                high ^= 1
                neg = 1
            else:
                neg = 0
            key = (low << es | high) << vsh | v
            n = unique.get(key)
            if n is None:
                if free:
                    n = free.pop()
                    var[n] = v
                    lo[n] = low
                    hi[n] = high
                else:
                    n = len(var)
                    var.append(v)
                    lo.append(low)
                    hi.append(high)
                unique[key] = n
            return n << 1 | neg

        def and_(f: int, g: int) -> int:
            if f == g:
                return f
            if f > g:
                f, g = g, f
            if f <= 1:
                return g if f == 0 else 1
            if f ^ g == 1:
                return 1
            key = f << es | g
            r = and_cache.get(key)
            if r is not None:
                return r
            nf = f >> 1
            ng = g >> 1
            vf = var[nf]
            vg = var[ng]
            if vf <= vg:
                c = f & 1
                f0 = lo[nf] ^ c
                f1 = hi[nf] ^ c
                v = vf
            else:
                f0 = f1 = f
                v = vg
            if vg == v:
                c = g & 1
                g0 = lo[ng] ^ c
                g1 = hi[ng] ^ c
            else:
                g0 = g1 = g
            r0 = and_(f0, g0)
            r1 = and_(f1, g1)
            r = mk(v, r0, r1) if r0 != r1 else r0
            and_cache[key] = r
            return r

        def or_(f: int, g: int) -> int:
            return and_(f ^ 1, g ^ 1) ^ 1

        def xor_(f: int, g: int) -> int:
            neg = (f ^ g) & 1
            f &= ~1
            g &= ~1
            if f == g:
                return 1 ^ neg  # x xor x = false
            if f > g:
                f, g = g, f
            if f == 0:  # TRUE xor g = not g
                return g ^ 1 ^ neg
            key = f << es | g
            r = xor_cache.get(key)
            if r is None:
                nf = f >> 1
                ng = g >> 1
                vf = var[nf]
                vg = var[ng]
                if vf <= vg:
                    f0 = lo[nf]
                    f1 = hi[nf]
                    v = vf
                else:
                    f0 = f1 = f
                    v = vg
                if vg == v:
                    g0 = lo[ng]
                    g1 = hi[ng]
                else:
                    g0 = g1 = g
                r = mk(v, xor_(f0, g0), xor_(f1, g1))
                xor_cache[key] = r
            return r ^ neg

        def ite_(f: int, g: int, h: int) -> int:
            if f <= 1:
                return g if f == 0 else h
            if g == h:
                return g
            if g == f:
                g = 0
            elif g == f ^ 1:
                g = 1
            if h == f:
                h = 1
            elif h == f ^ 1:
                h = 0
            if g == h:
                return g
            if g <= 1:
                if h <= 1:
                    return f if g == 0 else f ^ 1  # (g, h) is (1, 0) or (0, 1) here
                if g == 0:
                    return and_(f ^ 1, h ^ 1) ^ 1  # f | h
                return and_(f ^ 1, h)  # ~f & h
            if h <= 1:
                if h == 1:
                    return and_(f, g)
                return and_(f, g ^ 1) ^ 1  # ~f | g
            if g == h ^ 1:
                return xor_(f, h)
            if f & 1:
                f ^= 1
                g, h = h, g
            neg = g & 1
            if neg:
                g ^= 1
                h ^= 1
            key = ((f << es | g) << es) | h
            r = ite_cache.get(key)
            if r is None:
                nf, ng, nh = f >> 1, g >> 1, h >> 1
                vf, vg, vh = var[nf], var[ng], var[nh]
                v = vf
                if vg < v:
                    v = vg
                if vh < v:
                    v = vh
                if vf == v:
                    f0 = lo[nf]
                    f1 = hi[nf]
                else:
                    f0 = f1 = f
                if vg == v:
                    g0 = lo[ng]
                    g1 = hi[ng]
                else:
                    g0 = g1 = g
                if vh == v:
                    c = h & 1
                    h0 = lo[nh] ^ c
                    h1 = hi[nh] ^ c
                else:
                    h0 = h1 = h
                r = mk(v, ite_(f0, g0, h0), ite_(f1, g1, h1))
                ite_cache[key] = r
            return r ^ neg

        self._mk = mk
        self._and = and_
        self._or = or_
        self._xor = xor_
        self._ite = ite_

    # -- public boolean operations -------------------------------------------------------
    def _maybe_trim(self) -> None:
        for cache in (
            self._and_cache,
            self._xor_cache,
            self._ite_cache,
            self._ex_cache,
            self._ae_cache,
        ):
            if len(cache) > _CACHE_LIMIT:
                cache.clear()
        n = len(self._var)
        if n > self.peak_nodes:
            self.peak_nodes = n

    def NOT(self, f: int) -> int:
        """Negation."""
        return f ^ 1

    def AND(self, f: int, g: int) -> int:
        """Conjunction."""
        self._maybe_trim()
        return self._and(f, g)

    def OR(self, f: int, g: int) -> int:
        """Disjunction."""
        self._maybe_trim()
        return self._and(f ^ 1, g ^ 1) ^ 1

    def XOR(self, f: int, g: int) -> int:
        """Exclusive or."""
        self._maybe_trim()
        return self._xor(f, g)

    def IFF(self, f: int, g: int) -> int:
        """Equivalence."""
        return self.XOR(f, g) ^ 1

    def IMPLIES(self, f: int, g: int) -> int:
        """Implication."""
        self._maybe_trim()
        return self._and(f, g ^ 1) ^ 1

    def DIFF(self, f: int, g: int) -> int:
        """``f & ~g``."""
        self._maybe_trim()
        return self._and(f, g ^ 1)

    def ITE(self, f: int, g: int, h: int) -> int:
        """If-then-else."""
        self._maybe_trim()
        return self._ite(f, g, h)

    def and_all(self, fs: Iterable[int]) -> int:
        """Conjunction of several functions (balanced)."""
        items = list(fs)
        if not items:
            return TRUE
        self._maybe_trim()
        and_ = self._and
        while len(items) > 1:
            nxt = [and_(items[i], items[i + 1]) for i in range(0, len(items) - 1, 2)]
            if len(items) % 2:
                nxt.append(items[-1])
            items = nxt
        return items[0]

    def or_all(self, fs: Iterable[int]) -> int:
        """Disjunction of several functions (balanced)."""
        return self.and_all(f ^ 1 for f in fs) ^ 1

    def cube(self, assignment: Mapping[int, int | bool]) -> int:
        """The conjunction of literals ``level == value``."""
        mk = self._mk
        f = TRUE
        for v in sorted(assignment, reverse=True):
            self._check_level(v)
            f = mk(v, FALSE, f) if assignment[v] else mk(v, f, FALSE)
        return f

    # -- quantification ------------------------------------------------------------------
    def _as_varset(self, vs: VarSet | Iterable[int]) -> VarSet:
        return vs if isinstance(vs, VarSet) else self.varset(vs)

    def exists(self, f: int, vs: VarSet | Iterable[int]) -> int:
        """``exists vs. f``."""
        vs = self._as_varset(vs)
        self._maybe_trim()
        return self._exists_fn(vs)(f)

    def forall(self, f: int, vs: VarSet | Iterable[int]) -> int:
        """``forall vs. f``."""
        return self.exists(f ^ 1, vs) ^ 1

    def _exists_fn(self, vs: VarSet):
        var, lo, hi = self._var, self._lo, self._hi
        mk, and_ = self._mk, self._and
        cache = self._ex_cache
        mask, maxv, sid = vs.mask, vs.maxv, vs.id
        ssh = _SSHIFT

        def ex(f: int) -> int:
            if f <= 1:
                return f
            n = f >> 1
            v = var[n]
            if v > maxv:
                return f
            key = f << ssh | sid
            r = cache.get(key)
            if r is not None:
                return r
            c = f & 1
            f0 = lo[n] ^ c
            f1 = hi[n] ^ c
            if mask[v]:
                r0 = ex(f0)
                if r0 == 0:
                    r = 0
                else:
                    r = and_(r0 ^ 1, ex(f1) ^ 1) ^ 1
            else:
                r0 = ex(f0)
                r1 = ex(f1)
                r = mk(v, r0, r1) if r0 != r1 else r0
            cache[key] = r
            return r

        return ex

    def and_exists(self, f: int, g: int, vs: VarSet | Iterable[int]) -> int:
        """``exists vs. (f & g)`` without building ``f & g`` (relational product)."""
        vs = self._as_varset(vs)
        self._maybe_trim()
        var, lo, hi = self._var, self._lo, self._hi
        mk, and_ = self._mk, self._and
        ex = self._exists_fn(vs)
        cache = self._ae_cache
        mask, maxv, sid = vs.mask, vs.maxv, vs.id
        es, ssh = _ESHIFT, _SSHIFT

        def ae(f: int, g: int) -> int:
            if f == g:
                return ex(f)
            if f > g:
                f, g = g, f
            if f <= 1:
                return ex(g) if f == 0 else 1
            if f ^ g == 1:
                return 1
            nf = f >> 1
            ng = g >> 1
            vf = var[nf]
            vg = var[ng]
            v = vf if vf < vg else vg
            if v > maxv:
                return and_(f, g)
            key = (f << es | g) << ssh | sid
            r = cache.get(key)
            if r is not None:
                return r
            if vf == v:
                c = f & 1
                f0 = lo[nf] ^ c
                f1 = hi[nf] ^ c
            else:
                f0 = f1 = f
            if vg == v:
                c = g & 1
                g0 = lo[ng] ^ c
                g1 = hi[ng] ^ c
            else:
                g0 = g1 = g
            if mask[v]:
                r0 = ae(f0, g0)
                if r0 == 0:
                    r = 0
                else:
                    r = and_(r0 ^ 1, ae(f1, g1) ^ 1) ^ 1
            else:
                r0 = ae(f0, g0)
                r1 = ae(f1, g1)
                r = mk(v, r0, r1) if r0 != r1 else r0
            cache[key] = r
            return r

        return ae(f, g)

    # -- substitution --------------------------------------------------------------------
    def restrict(self, f: int, assignment: Mapping[int, int | bool]) -> int:
        """The cofactor of ``f`` by a partial assignment ``{level: value}``."""
        if not assignment:
            return f
        self._maybe_trim()
        var, lo, hi, mk = self._var, self._lo, self._hi, self._mk
        maxv = max(assignment)
        val = {v: bool(b) for v, b in assignment.items()}
        memo: dict[int, int] = {}

        def rec(f: int) -> int:
            if f <= 1:
                return f
            n = f >> 1
            v = var[n]
            if v > maxv:
                return f
            r = memo.get(n)
            if r is None:
                b = val.get(v)
                if b is None:
                    r0 = rec(lo[n])
                    r1 = rec(hi[n])
                    r = mk(v, r0, r1) if r0 != r1 else r0
                else:
                    r = rec(hi[n] if b else lo[n])
                memo[n] = r
            return r ^ (f & 1)

        return rec(f)

    def simplify(self, f: int, care: int) -> int:
        """A function that agrees with ``f`` wherever ``care`` holds, usually smaller (the
        Coudert-Madre *restrict* operator). ``care`` must not be FALSE."""
        if care == FALSE:
            raise ValueError("simplify needs a satisfiable care set")
        self._maybe_trim()
        var, lo, hi, mk, and_ = self._var, self._lo, self._hi, self._mk, self._and
        memo: dict[tuple[int, int], int] = {}

        def rec(f: int, c: int) -> int:
            if c == 0 or f <= 1:
                return f
            if f == c:
                return 0
            if f ^ c == 1:
                return 1
            key = (f, c)
            r = memo.get(key)
            if r is not None:
                return r
            nf = f >> 1
            nc = c >> 1
            vf = var[nf]
            vc = var[nc]
            k = c & 1
            c0 = lo[nc] ^ k
            c1 = hi[nc] ^ k
            if vc < vf:
                r = rec(f, and_(c0 ^ 1, c1 ^ 1) ^ 1)
            else:
                k = f & 1
                f0 = lo[nf] ^ k
                f1 = hi[nf] ^ k
                if vc > vf:
                    c0 = c1 = c
                if c0 == 1:
                    r = rec(f1, c1)
                elif c1 == 1:
                    r = rec(f0, c0)
                else:
                    r0 = rec(f0, c0)
                    r1 = rec(f1, c1)
                    r = mk(vf, r0, r1) if r0 != r1 else r0
            memo[key] = r
            return r

        return rec(f, care)

    def compose(self, f: int, mapping: Mapping[int, int]) -> int:
        """Substitute, simultaneously, the function ``mapping[v]`` for each variable ``v``
        in ``f``."""
        if not mapping:
            return f
        self._maybe_trim()
        var, lo, hi, mk, ite = self._var, self._lo, self._hi, self._mk, self._ite
        maxv = max(mapping)
        memo: dict[int, int] = {}
        get = mapping.get

        def rec(f: int) -> int:
            if f <= 1:
                return f
            n = f >> 1
            v = var[n]
            if v > maxv:
                return f
            r = memo.get(n)
            if r is None:
                r0 = rec(lo[n])
                r1 = rec(hi[n])
                g = get(v)
                if g is None:
                    g = mk(v, 1, 0)
                r = ite(g, r1, r0)
                memo[n] = r
            return r ^ (f & 1)

        return rec(f)

    def rename(self, f: int, mapping: Mapping[int, int]) -> int:
        """Replace variable ``v`` by variable ``mapping[v]``. Fast when the renaming keeps
        the relative order of the variables of ``f``; correct in any case."""
        if not mapping:
            return f
        self._maybe_trim()
        var, lo, hi, mk, ite = self._var, self._lo, self._hi, self._mk, self._ite
        for w in mapping.values():
            self._check_level(w)
        maxv = max(mapping)
        memo: dict[int, int] = {}
        get = mapping.get

        def rec(f: int) -> int:
            if f <= 1:
                return f
            n = f >> 1
            v = var[n]
            if v > maxv:
                return f
            r = memo.get(n)
            if r is None:
                r0 = rec(lo[n])
                r1 = rec(hi[n])
                w = get(v, v)
                if w < var[r0 >> 1] and w < var[r1 >> 1]:
                    r = mk(w, r0, r1) if r0 != r1 else r0
                else:
                    r = ite(mk(w, 1, 0), r1, r0)
                memo[n] = r
            return r ^ (f & 1)

        return rec(f)

    def transfer(self, f: int, other: BDD, mapping: Mapping[int, int] | None = None) -> int:
        """Copy ``f`` into the manager ``other``, sending level ``v`` to ``mapping[v]``
        (default: the same level); the orders may differ."""
        var, lo, hi = self._var, self._lo, self._hi
        memo: dict[int, int] = {}
        get = (lambda v: v) if mapping is None else mapping.__getitem__

        def rec(f: int) -> int:
            if f <= 1:
                return f
            n = f >> 1
            r = memo.get(n)
            if r is None:
                r0 = rec(lo[n])
                r1 = rec(hi[n])
                r = other.ITE(other.var(get(var[n])), r1, r0)
                memo[n] = r
            return r ^ (f & 1)

        return rec(f)

    # -- queries -------------------------------------------------------------------------
    def evaluate(self, f: int, value: Mapping[int, int] | Sequence[int]) -> bool:
        """``f`` under a total assignment (a mapping or a sequence indexed by level; levels
        missing from a mapping read as 0)."""
        var, lo, hi = self._var, self._lo, self._hi
        if isinstance(value, Mapping):
            get = value.get

            def bit(v: int) -> int:
                return get(v, 0)
        else:
            bit = value.__getitem__
        c = f & 1
        n = f >> 1
        while n:
            e = hi[n] if bit(var[n]) else lo[n]
            c ^= e & 1
            n = e >> 1
        return c == 0

    def pick_one(self, f: int, levels: Iterable[int] = ()) -> dict[int, int] | None:
        """A satisfying assignment of ``f`` (``None`` if ``f`` is FALSE) as ``{level: bit}``
        covering the variables on the chosen path and every level in ``levels`` (0 where
        free). The 0 branch is preferred, so the result is the least in that order."""
        if f == FALSE:
            return None
        out = dict.fromkeys(levels, 0)
        var, lo, hi = self._var, self._lo, self._hi
        while f > 1:
            n = f >> 1
            c = f & 1
            f0 = lo[n] ^ c
            if f0 != FALSE:
                out[var[n]] = 0
                f = f0
            else:
                out[var[n]] = 1
                f = hi[n] ^ c
        return out

    def support(self, f: int | Iterable[int]) -> set[int]:
        """Levels of the variables ``f`` (or any of several functions) depends on."""
        roots = [f] if isinstance(f, int) else list(f)
        seen: set[int] = set()
        out: set[int] = set()
        stack = [e >> 1 for e in roots]
        var, lo, hi = self._var, self._lo, self._hi
        while stack:
            n = stack.pop()
            if n == 0 or n in seen:
                continue
            seen.add(n)
            out.add(var[n])
            stack.append(lo[n] >> 1)
            stack.append(hi[n] >> 1)
        return out

    def node_count(self, f: int | Iterable[int]) -> int:
        """Distinct nodes (the constant included) reachable from ``f`` or several roots."""
        roots = [f] if isinstance(f, int) else list(f)
        seen: set[int] = set()
        stack = [e >> 1 for e in roots]
        lo, hi = self._lo, self._hi
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            if n:
                stack.append(lo[n] >> 1)
                stack.append(hi[n] >> 1)
        return len(seen)

    def count(self, f: int, levels: Iterable[int]) -> int:
        """The number of assignments to ``levels`` satisfying ``f``. ``f`` must depend only
        on variables in ``levels``."""
        order = sorted(set(levels))
        pos = {v: i for i, v in enumerate(order)}
        total = len(order)
        var, lo, hi = self._var, self._lo, self._hi
        memo: dict[int, int] = {0: 1}

        def at(n: int) -> int:
            v = var[n]
            if n == 0:
                return total
            p = pos.get(v)
            if p is None:
                raise ValueError(f"count: the function depends on level {v}, not in the set")
            return p

        def rec(n: int) -> int:
            r = memo.get(n)
            if r is None:
                p = at(n)
                r = sub(lo[n], p + 1) + sub(hi[n], p + 1)
                memo[n] = r
            return r

        def sub(e: int, p: int) -> int:
            n = e >> 1
            q = at(n)
            c = rec(n)
            if e & 1:
                c = (1 << (total - q)) - c
            return c << (q - p)

        return sub(f, 0)

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

    def register(self, holder: object) -> None:
        """Keep the edges returned by ``holder.bdd_roots()`` alive while ``holder`` lives."""
        self._holders.add(holder)

    def gc(self, roots: Iterable[int] = ()) -> int:
        """Reclaim every node not reachable from ``roots``, protected edges and registered
        holders; clear the computed tables. Returns the number of nodes freed."""
        var, lo, hi = self._var, self._lo, self._hi
        n_total = len(var)
        mark = bytearray(n_total)
        mark[0] = 1
        stack = [e >> 1 for e in roots]
        stack.extend(self._protected)
        for holder in list(self._holders):
            stack.extend(e >> 1 for e in holder.bdd_roots())
        while stack:
            n = stack.pop()
            if mark[n]:
                continue
            mark[n] = 1
            stack.append(lo[n] >> 1)
            stack.append(hi[n] >> 1)
        for n in self._free:
            mark[n] = 2  # already free
        unique = self._unique
        es, vsh = _ESHIFT, _VSHIFT
        freed = 0
        free = self._free
        for n in range(1, n_total):
            if not mark[n]:
                del unique[(lo[n] << es | hi[n]) << vsh | var[n]]
                var[n] = _TERMVAR
                lo[n] = 0
                hi[n] = 0
                free.append(n)
                freed += 1
        for cache in (
            self._and_cache,
            self._xor_cache,
            self._ite_cache,
            self._ex_cache,
            self._ae_cache,
        ):
            cache.clear()
        self.gc_runs += 1
        return freed

    def stats(self) -> dict[str, int]:
        """Counters: live nodes, node-table high-water mark, cache sizes, collections."""
        return {
            "live_nodes": self.live_nodes,
            "peak_nodes": max(self.peak_nodes, len(self._var)),
            "unique": len(self._unique),
            "and_cache": len(self._and_cache),
            "ite_cache": len(self._ite_cache),
            "gc_runs": self.gc_runs,
            "vars": self.num_vars,
        }
