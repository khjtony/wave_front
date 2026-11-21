"""A BDD manager on top of CUDD, with dynamic variable reordering: the interface of the
reference manager :class:`wavefront.symbolic.bdd.BDD` (an engineering spike, see
docs/engine_reordering_spike.md).

**Edges.** An edge is the same kind of ``int`` as in the other cores: ``(handle << 1) |
complement``, TRUE 0, FALSE 1, so callers negate with ``^ 1`` and compare functions with
``==``. A handle names one regular CUDD node, and the wrapper keeps one CUDD reference per
handle. A table from node address to handle makes the handle of a function unique, so equal
edges are equal functions, as in the other cores. CUDD's reordering rewrites nodes in place
and keeps the function of every referenced node, so handles stay valid across a reordering.

**Variable identity.** What the callers of this interface call a *level* (the number
:meth:`BDD.add_var` returns, the keys of ``compose``, ``rename``, ``restrict`` and ``cube``,
the members of a variable set, the elements of ``support``, the positions of an ``evaluate``
array) is CUDD's variable *index* here: it is fixed when the variable is created and does not
change when reordering moves the variable. The current place of a variable in the order is
its *position* (:meth:`BDD.position`, :meth:`BDD.order`). With reordering off the two are
equal and every result equals the other cores'. With reordering on:

- functions, ``support``, ``count``, ``evaluate`` and ``pick_one`` are unchanged (``pick_one``
  walks the support in level order, taking 0 where it can, whatever the current order);
- ``node_count``, ``top``, ``low`` and ``high`` describe the BDD in the current order, so node
  counts differ from the other cores' and ``top`` is the variable at the root, not the least
  level of the support.

**Garbage collection.** CUDD frees by reference count. :meth:`BDD.gc` has the reference's
roots (its arguments, protected edges, registered holders): it gives up the reference of
every other handle, after which those edges are invalid, as in the other cores.
:meth:`BDD.maybe_gc` does that once the live nodes pass ``min(gc_min_nodes,
release_min_nodes)``: giving references back is cheap, and a handle that is kept needlessly
costs memory and reordering time. ``gc_factor`` is not used.

**Reordering** (``reorder=`` or ``WAVEFRONT_CUDD_REORDER``): ``"off"`` (default); ``"auto"``,
CUDD's automatic reordering inside operations; ``"points"``, reordering only at
:meth:`BDD.maybe_gc`, when only rooted functions are alive. :meth:`BDD.reorder` runs one
pass on request in any mode. :meth:`BDD.group` ties variables together (the encoding groups
each current-state bit with its next-state bit).

Differences from the reference in results: ``simplify`` is CUDD's ``Cudd_bddRestrict``, which
agrees with ``f`` on the care set but need not return the reference's function.

Importing this module raises :class:`ImportError` when the binding is not built
(``python -m wavefront.symbolic._cudd.build``) or was built from other sources.
"""

from __future__ import annotations

import os
import resource
import weakref
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager

from ._cudd import HERE, SOURCES, source_hash
from .bdd import _TERMVAR, FALSE, TRUE, VarSet

try:
    from ._cudd._cudd import ffi, lib
except ImportError as exc:  # not built
    raise ImportError(
        f"the CUDD binding is not built ({exc}); run python -m wavefront.symbolic._cudd.build"
    ) from exc

if all((HERE / name).exists() for name in SOURCES):
    _built = ffi.string(lib.wf_source_hash()).decode()
    if _built != source_hash():
        raise ImportError(
            f"the CUDD binding is stale (built from sources {_built}, now {source_hash()}); "
            "rerun python -m wavefront.symbolic._cudd.build"
        )

__all__ = ["BDD", "TRUE", "FALSE", "REORDER_MODES", "METHODS"]

if os.environ.get("WAVEFRONT_CUDD_BACKTRACE") == "1":  # a C stack on stderr if CUDD crashes
    lib.wf_trace_crashes()

REORDER_MODES = ("off", "auto", "points")
METHODS = {
    "sift": lib.WF_SIFT,
    "sift_converge": lib.WF_SIFT_CONVERGE,
    "group_sift": lib.WF_GROUP_SIFT,
    "group_sift_converge": lib.WF_GROUP_SIFT_CONVERGE,
}
_NSTATS = lib.WF_NSTATS
_new = ffi.new
_from_buffer = ffi.from_buffer


def _oom() -> MemoryError:
    return MemoryError("CUDD returned no result (out of memory, or past its memory limit)")


def _default_max_memory() -> int:
    """Bytes CUDD may use: ``WAVEFRONT_CUDD_MAX_MEMORY_MB``, else four fifths of the
    address-space limit of the process when it has one, else CUDD's own default (0)."""
    env = os.environ.get("WAVEFRONT_CUDD_MAX_MEMORY_MB")
    if env:
        return int(float(env) * 1024 * 1024)
    soft, _ = resource.getrlimit(resource.RLIMIT_AS)
    return 0 if soft == resource.RLIM_INFINITY else int(soft * 0.8)


class BDD:
    """A BDD manager backed by CUDD; the interface of :class:`wavefront.symbolic.bdd.BDD`."""

    TRUE = TRUE
    FALSE = FALSE
    core = "cudd"

    def __init__(
        self,
        reorder: str | None = None,
        method: str | None = None,
        max_memory: int | None = None,
        grouping: bool | None = None,
    ) -> None:
        env = os.environ.get
        reorder = reorder or env("WAVEFRONT_CUDD_REORDER") or "off"
        method = method or env("WAVEFRONT_CUDD_METHOD") or "group_sift"
        if reorder not in REORDER_MODES:
            raise ValueError(f"unknown reordering mode {reorder!r} (one of {REORDER_MODES})")
        if method not in METHODS:
            raise ValueError(f"unknown reordering method {method!r} (one of {tuple(METHODS)})")
        if grouping is None:
            grouping = env("WAVEFRONT_CUDD_GROUP", "1") != "0"
        if max_memory is None:
            max_memory = _default_max_memory()
        dd = lib.wf_new(max_memory, 0)
        if dd == ffi.NULL:
            raise _oom()
        self._dd = ffi.gc(dd, lib.wf_delete)
        self.reorder_mode = reorder
        self.method = method
        self.grouping = grouping
        self.max_memory = max_memory
        growth = env("WAVEFRONT_CUDD_MAX_GROWTH")
        if growth:
            lib.wf_set_max_growth(self._dd, float(growth))
        one = lib.wf_one(self._dd)
        self._ptr: list[int] = [one]  # handle -> regular node address (0: a free handle)
        self._h: dict[int, int] = {one: 0}  # regular node address -> handle
        self._free: list[int] = []
        self._varptr: list[int] = []  # level -> address of the projection function
        self.names: list[str] = []
        self._varsets: dict[tuple[int, ...], VarSet] = {}
        self._cubes: list[int] = []  # variable-set id -> address of its cube
        self._protected: dict[int, int] = {}
        self._holders: weakref.WeakSet = weakref.WeakSet()
        self._groups: list[tuple[int, ...]] = []
        self.gc_min_nodes = 2_000_000
        self.gc_factor = 2.0  # kept for the interface; not used
        self.release_min_nodes = int(env("WAVEFRONT_CUDD_RELEASE_MIN_NODES") or 100_000)
        self.reorder_min_nodes = int(env("WAVEFRONT_CUDD_REORDER_MIN_NODES") or 50_000)
        self._next_reorder = self.reorder_min_nodes
        self._gc_runs = 0
        self.reorder_log: list[dict] = []
        if reorder == "auto":
            lib.wf_autodyn(self._dd, 1, METHODS[method])
            first = env("WAVEFRONT_CUDD_FIRST_REORDER")
            if first:  # CUDD's default is 4004 nodes
                lib.wf_set_next_reordering(self._dd, int(first))

    # -- handles -------------------------------------------------------------------------
    def _wrap(self, r: int) -> int:
        """The edge of a referenced CUDD result; the reference is kept by a new handle or
        given back when the node already has one."""
        if r == 0:
            raise _oom()
        reg = r & -2
        h = self._h.get(reg)
        if h is None:
            if self._free:
                h = self._free.pop()
                self._ptr[h] = reg
            else:
                h = len(self._ptr)
                self._ptr.append(reg)
            self._h[reg] = h
        else:
            lib.wf_deref(self._dd, reg)
        return (h << 1) | (r & 1)

    def _p(self, e: int) -> int:
        """CUDD's pointer for an edge."""
        reg = self._ptr[e >> 1]
        if not reg:
            raise ValueError(f"stale BDD edge {e} (released by a collection)")
        return reg | (e & 1)

    def _ps(self, edges: Sequence[int]):
        return _new("uintptr_t[]", [self._p(e) for e in edges]) if edges else ffi.NULL

    # -- variables -----------------------------------------------------------------------
    @property
    def num_vars(self) -> int:
        """Number of variables created."""
        return len(self.names)

    def add_var(self, name: str | None = None) -> int:
        """Create a variable at the bottom of the order; return its level (its permanent
        identity, see the module docstring)."""
        level = len(self.names)
        if lib.wf_add_var(self._dd) != level:
            raise ValueError("too many BDD variables")
        p = lib.wf_var(self._dd, level)
        if p == 0:
            raise _oom()
        self._varptr.append(p)
        self.names.append(name if name is not None else f"x{level}")
        return level

    def var(self, level: int) -> int:
        """The function that is true when variable ``level`` is 1."""
        self._check_level(level)
        p = self._varptr[level]
        lib.wf_ref(p)
        return self._wrap(p)

    def nvar(self, level: int) -> int:
        """The function that is true when variable ``level`` is 0."""
        return self.var(level) ^ 1

    def _check_level(self, level: int) -> None:
        if not 0 <= level < len(self.names):
            raise ValueError(f"no BDD variable at level {level}")

    def varset(self, levels: Iterable[int]) -> VarSet:
        """The (cached) :class:`~wavefront.symbolic.bdd.VarSet` of ``levels``."""
        key = tuple(sorted(set(levels)))
        vs = self._varsets.get(key)
        if vs is None:
            mask = bytearray(len(self.names) + 1)
            for v in key:
                self._check_level(v)
                mask[v] = 1
            indices = _new("int[]", key) if key else ffi.NULL
            cube = lib.wf_cube(self._dd, indices, ffi.NULL, len(key))
            if cube == 0:
                raise _oom()
            vs = VarSet(len(self._cubes), key, mask, key[-1] if key else -1)
            self._cubes.append(cube)
            self._varsets[key] = vs
        return vs

    def _as_varset(self, vs: VarSet | Iterable[int]) -> VarSet:
        if isinstance(vs, VarSet):
            return vs if self._varsets.get(vs.levels) is vs else self.varset(vs.levels)
        return self.varset(vs)

    # -- the order -----------------------------------------------------------------------
    def position(self, level: int) -> int:
        """The current place of variable ``level`` in the order (0 is the top)."""
        self._check_level(level)
        return lib.wf_position(self._dd, level)

    def order(self) -> list[int]:
        """The variables (levels) from the top of the current order to the bottom."""
        return sorted(range(len(self.names)), key=self.position)

    def group(self, levels: Iterable[int]) -> bool:
        """Keep the variables ``levels`` adjacent, in their present relative order, under
        reordering (they must be adjacent now). A no-op returning ``False`` when the manager
        was made with ``grouping=False``. Call it once every variable exists and before the
        first reordering."""
        members = sorted(set(levels), key=self.position)
        if not self.grouping or len(members) < 2:
            return False
        first = self.position(members[0])
        if [self.position(v) for v in members] != list(range(first, first + len(members))):
            raise ValueError(f"cannot group {members}: the variables are not adjacent")
        if not lib.wf_group(self._dd, members[0], len(members)):
            raise _oom()
        self._groups.append(tuple(members))
        return True

    def reorder(self, method: str | None = None) -> tuple[int, int]:
        """One reordering pass now, over everything CUDD holds alive (collect first, with
        :meth:`gc`, so that only what is in use is counted). Returns the live nodes before
        and after."""
        before = self.live_nodes
        t0 = self._raw_stats()[9]
        if not lib.wf_reorder(self._dd, METHODS[method or self.method], 0):
            raise _oom()
        after = self.live_nodes
        self._next_reorder = max(self.reorder_min_nodes, 2 * after)
        self.reorder_log.append({"before": before, "after": after, "ms": self._raw_stats()[9] - t0})
        return before, after

    def shuffle(self, order: Sequence[int]) -> None:
        """Impose an order (the levels from top to bottom). For tests: CUDD does not check
        the groups of :meth:`group` here."""
        if sorted(order) != list(range(len(self.names))):
            raise ValueError("shuffle needs every level exactly once")
        if not lib.wf_shuffle(self._dd, _new("int[]", list(order))):
            raise _oom()

    def check(self) -> bool:
        """CUDD's own consistency checks of its tables (slow; for tests)."""
        return lib.wf_check(self._dd) == 0

    # -- node inspection -----------------------------------------------------------------
    def top(self, f: int) -> int:
        """The level of the variable at the root of ``f`` in the current order (a large
        number for constants)."""
        t = lib.wf_top(self._p(f))
        return _TERMVAR if t > _TERMVAR else t

    def _child(self, f: int, which) -> int:
        p = self._p(f)
        if lib.wf_is_const(p):
            return f
        r = which(p & -2) ^ (p & 1)
        lib.wf_ref(r)
        return self._wrap(r)

    def low(self, f: int) -> int:
        """The 0-cofactor of ``f`` with respect to the variable at its root."""
        return self._child(f, lib.wf_else)

    def high(self, f: int) -> int:
        """The 1-cofactor of ``f`` with respect to the variable at its root."""
        return self._child(f, lib.wf_then)

    @property
    def live_nodes(self) -> int:
        """Nodes CUDD holds alive (referenced, directly or from a referenced node)."""
        return self._raw_stats()[0]

    @property
    def peak_nodes(self) -> int:
        """CUDD's high-water mark of live nodes."""
        return self._raw_stats()[1]

    @property
    def gc_runs(self) -> int:
        """Collections run through :meth:`gc` (CUDD's own are in :meth:`stats`)."""
        return self._gc_runs

    # -- boolean operations --------------------------------------------------------------
    def NOT(self, f: int) -> int:
        """Negation."""
        return f ^ 1

    def AND(self, f: int, g: int) -> int:
        """Conjunction."""
        return self._wrap(lib.wf_and(self._dd, self._p(f), self._p(g)))

    def OR(self, f: int, g: int) -> int:
        """Disjunction."""
        return self._wrap(lib.wf_and(self._dd, self._p(f ^ 1), self._p(g ^ 1))) ^ 1

    def XOR(self, f: int, g: int) -> int:
        """Exclusive or."""
        return self._wrap(lib.wf_xor(self._dd, self._p(f), self._p(g)))

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
        return self._wrap(lib.wf_ite(self._dd, self._p(f), self._p(g), self._p(h)))

    def and_all(self, fs: Iterable[int]) -> int:
        """Conjunction of several functions (balanced)."""
        items = list(fs)
        if not items:
            return TRUE
        if len(items) == 1:
            return items[0]
        return self._wrap(lib.wf_and_all(self._dd, self._ps(items), len(items)))

    def or_all(self, fs: Iterable[int]) -> int:
        """Disjunction of several functions (balanced)."""
        return self.and_all(f ^ 1 for f in fs) ^ 1

    def _cube(self, assignment: Mapping[int, int | bool]) -> int:
        """A referenced CUDD cube of the literals ``level == value``."""
        levels = list(assignment)
        for v in levels:
            self._check_level(v)
        vals = bytes(1 if assignment[v] else 0 for v in levels)
        if not levels:
            return lib.wf_one(self._dd)
        r = lib.wf_cube(
            self._dd, _new("int[]", levels), _from_buffer("uint8_t[]", vals), len(levels)
        )
        if r == 0:
            raise _oom()
        return r

    def cube(self, assignment: Mapping[int, int | bool]) -> int:
        """The conjunction of literals ``level == value``."""
        return self._wrap(self._cube(assignment))

    # -- quantification ------------------------------------------------------------------
    def exists(self, f: int, vs: VarSet | Iterable[int]) -> int:
        """``exists vs. f``."""
        vs = self._as_varset(vs)
        return self._wrap(lib.wf_exists(self._dd, self._p(f), self._cubes[vs.id]))

    def forall(self, f: int, vs: VarSet | Iterable[int]) -> int:
        """``forall vs. f``."""
        return self.exists(f ^ 1, vs) ^ 1

    def and_exists(self, f: int, g: int, vs: VarSet | Iterable[int]) -> int:
        """``exists vs. (f & g)`` without building ``f & g`` (relational product)."""
        vs = self._as_varset(vs)
        return self._wrap(lib.wf_and_exists(self._dd, self._p(f), self._p(g), self._cubes[vs.id]))

    # -- substitution --------------------------------------------------------------------
    def restrict(self, f: int, assignment: Mapping[int, int | bool]) -> int:
        """The cofactor of ``f`` by a partial assignment ``{level: value}``."""
        if not assignment:
            return f
        cube = self._cube(assignment)
        try:
            return self._wrap(lib.wf_cofactor(self._dd, self._p(f), cube))
        finally:
            lib.wf_deref(self._dd, cube)

    def simplify(self, f: int, care: int) -> int:
        """A function that agrees with ``f`` wherever ``care`` holds, usually smaller
        (CUDD's ``Cudd_bddRestrict``). ``care`` must not be FALSE."""
        if care == FALSE:
            raise ValueError("simplify needs a satisfiable care set")
        return self._wrap(lib.wf_simplify(self._dd, self._p(f), self._p(care)))

    def compose(self, f: int, mapping: Mapping[int, int]) -> int:
        """Substitute, simultaneously, the function ``mapping[v]`` for each variable ``v``
        in ``f``."""
        if not mapping:
            return f
        levels = list(mapping)
        for v in levels:
            self._check_level(v)
        fns = _new("uintptr_t[]", [self._p(mapping[v]) for v in levels])
        return self._wrap(
            lib.wf_compose(self._dd, self._p(f), _new("int[]", levels), fns, len(levels))
        )

    def rename(self, f: int, mapping: Mapping[int, int]) -> int:
        """Replace variable ``v`` by variable ``mapping[v]``."""
        if not mapping:
            return f
        for w in mapping.values():
            self._check_level(w)
        levels = [v for v in mapping if 0 <= v < len(self.names)]
        fns = _new("uintptr_t[]", [self._varptr[mapping[v]] for v in levels])
        if not levels:
            return f
        return self._wrap(
            lib.wf_compose(self._dd, self._p(f), _new("int[]", levels), fns, len(levels))
        )

    def _nodes(self, f: int) -> list[tuple[int, int, int, int]]:
        """The nodes under ``f`` as ``(address, level, low, high)``, children first; ``low``
        and ``high`` are CUDD pointers (complement in the low bit)."""
        root = self._p(f) & -2
        seen: set[int] = set()
        out: list[tuple[int, int, int, int]] = []
        stack: list[tuple[int, bool]] = [(root, False)]
        top, then_, else_, const = lib.wf_top, lib.wf_then, lib.wf_else, lib.wf_is_const
        while stack:
            p, done = stack.pop()
            if done:
                out.append((p, top(p), else_(p), then_(p)))
                continue
            if p in seen or const(p):
                continue
            seen.add(p)
            stack.append((p, True))
            stack.append((else_(p) & -2, False))
            stack.append((then_(p), False))
        return out

    def transfer(self, f: int, other: object, mapping: Mapping[int, int] | None = None) -> int:
        """Copy ``f`` into the manager ``other`` (of any core), sending level ``v`` to
        ``mapping[v]`` (default: the same level); the orders may differ."""
        get = (lambda v: v) if mapping is None else mapping.__getitem__
        memo: dict[int, int] = {self._ptr[0]: TRUE}
        for p, v, lo, hi in self._nodes(f):
            r0 = memo[lo & -2] ^ (lo & 1)
            r1 = memo[hi]
            memo[p] = other.ITE(other.var(get(v)), r1, r0)  # type: ignore[attr-defined]
        return memo[self._p(f) & -2] ^ (f & 1)

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
        r = lib.wf_evaluate(self._dd, self._p(f), _from_buffer("uint8_t[]", bits), len(bits))
        if r < 0:
            raise IndexError("evaluate: the assignment is shorter than a level it needs")
        return r == 1

    def pick_one(self, f: int, levels: Iterable[int] = ()) -> dict[int, int] | None:
        """A satisfying assignment of ``f`` (``None`` if ``f`` is FALSE) as ``{level: bit}``:
        the one the reference picks under the order of creation, whatever the current
        order. It covers the variables it had to decide and every level in ``levels`` (0
        where free)."""
        if f == FALSE:
            return None
        out = dict.fromkeys(levels, 0)
        cap = len(self.names) + 1
        lv = _new("int[]", cap)
        bits = _new("uint8_t[]", cap)
        k = lib.wf_pick_one(self._dd, self._p(f), lv, bits, cap)
        if k < 0:
            raise _oom()
        for i in range(k):
            out[lv[i]] = bits[i]
        return out

    def support(self, f: int | Iterable[int]) -> set[int]:
        """Levels of the variables ``f`` (or any of several functions) depends on."""
        roots = [f] if isinstance(f, int) else list(f)
        n = len(self.names)
        if not roots or not n:
            return set()
        out = bytearray(n)
        k = lib.wf_support(self._dd, self._ps(roots), len(roots), _from_buffer("uint8_t[]", out), n)
        if k < 0:
            raise _oom()
        return {v for v, b in enumerate(out) if b}

    def node_count(self, f: int | Iterable[int]) -> int:
        """Distinct nodes (the constant included) reachable from ``f`` or several roots, in
        the current order."""
        roots = [f] if isinstance(f, int) else list(f)
        if not roots:
            return 0
        return lib.wf_node_count(self._ps(roots), len(roots))

    def count(self, f: int, levels: Iterable[int]) -> int:
        """The number of assignments to ``levels`` satisfying ``f``. ``f`` must depend only
        on variables in ``levels``."""
        chosen = set(levels)
        outside = self.support(f) - chosen
        if outside:
            raise ValueError(f"count: the function depends on level {min(outside)}, not in the set")
        total = len(chosen)
        limbs = total // 32 + 2
        out = _new("uint32_t[]", limbs)
        if lib.wf_count(self._dd, self._p(f), total, out, limbs) != 0:
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
        """Give up every handle that is not a root (``roots``, protected edges, registered
        holders); CUDD then frees what nothing references. Returns the number of nodes that
        stopped being alive."""
        keep = {0}
        keep.update(e >> 1 for e in roots)
        keep.update(self._protected)
        for holder in list(self._holders):
            keep.update(e >> 1 for e in holder.bdd_roots())
        ptr = self._ptr
        dead = [h for h in range(1, len(ptr)) if ptr[h] and h not in keep]
        before = self.live_nodes
        if dead:
            addrs = [ptr[h] for h in dead]
            for h, p in zip(dead, addrs, strict=True):
                del self._h[p]
                ptr[h] = 0
            self._free.extend(reversed(dead))
            lib.wf_deref_many(self._dd, _new("uintptr_t[]", addrs), len(addrs))
        self._gc_runs += 1
        return max(before - self.live_nodes, 0)

    def maybe_gc(self, roots: Iterable[int] = ()) -> bool:
        """Run :meth:`gc` if the live nodes exceed ``min(gc_min_nodes, release_min_nodes)``;
        in the ``"points"`` mode, reorder afterwards when what is left has outgrown the
        result of the previous reordering. Callers pass every edge they still need that is
        not protected or held by a registered holder."""
        if self.live_nodes <= min(self.gc_min_nodes, self.release_min_nodes):
            return False
        self.gc(roots)
        if self.reorder_mode == "points" and self.live_nodes > self._next_reorder:
            self.reorder()
        return True

    def close(self) -> int:
        """Give up every reference this wrapper holds and return the number of nodes CUDD
        still counts as referenced (0 unless a reference leaked). The manager must not be
        used afterwards. For tests."""
        self._protected.clear()
        self._holders = weakref.WeakSet()
        self.gc()
        for p in self._cubes:
            lib.wf_deref(self._dd, p)
        for p in self._varptr:
            lib.wf_deref(self._dd, p)
        lib.wf_deref(self._dd, self._ptr[0])
        self._cubes, self._varptr, self._ptr, self._h = [], [], [0], {}
        self._varsets = {}
        return lib.wf_check_zero_ref(self._dd)

    def _raw_stats(self) -> list[int]:
        out = _new("uint64_t[]", _NSTATS)
        lib.wf_stats(self._dd, out)
        return list(out)

    def stats(self) -> dict[str, int]:
        """Counters: live nodes and their high-water mark, CUDD's node table (with dead
        nodes) and its high-water mark, bytes in use, cache slots, collections, reorderings
        and the milliseconds spent in each."""
        s = self._raw_stats()
        return {
            "live_nodes": s[0],
            "peak_nodes": s[1],
            "unique": s[3],
            "gc_runs": self._gc_runs,
            "vars": s[10],
            "peak_table_nodes": s[2],
            "dead_nodes": s[4],
            "memory_bytes": s[5],
            "cache_slots": s[6],
            "cudd_gc_runs": s[7],
            "cudd_gc_ms": s[11],
            "reorderings": s[8],
            "reorder_ms": s[9],
            "handles": len(self._h),
        }
