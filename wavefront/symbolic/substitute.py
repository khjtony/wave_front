"""Substitution level by level: :meth:`BDD.compose` split into one ``ITE`` per node of the
target, with every sub-result released as soon as its last parent is done.

``compose(f, mapping)`` computes, for every node ``n`` of ``f`` with variable ``v`` and
children ``lo`` and ``hi``, the sub-result ``r(n) = ITE(mapping[v], r(hi), r(lo))``, bottom
up, and returns ``r(root)``. Inside one manager call nothing can be collected, so every
sub-result stays in the node table until the call returns. When the substituted functions
read variables far above the variable they replace (the next-state functions of a game read
the action bits and state bits of the whole order), a sub-result is a graph over all of them
and shares little with the other sub-results: on the largest model the sub-results together
are 20 to 37 times the size of the result, and they, not the result, set the memory of a
controllable predecessor (docs/engine_split_step.md).

:func:`compose_by_levels` computes the same sub-results by the same recursion, with one
``ITE`` call per node, in the order of the levels from the bottom of ``f`` to its top. A
sub-result is needed by the parents of its node only, so it is dropped when the last of
them is done, and the manager may collect between two nodes. What must be alive at any time
is the sub-results of the nodes below the level in work that still have a parent at or above
it: at most the width of ``f`` at that level, not the whole of ``f``.

The result is the edge :meth:`BDD.compose` returns: the sub-results are the same functions,
and a manager has one edge per function.
"""

from __future__ import annotations

from array import array
from collections.abc import Iterable, Mapping
from itertools import chain

__all__ = ["compose_by_levels", "STATIC_CORES"]

# The cores this runs on: a level is a place in a fixed order, and an edge stays valid
# while its node is reachable from a root of a collection. Neither holds in the CUDD binding
# (levels are variable indices that reordering moves, and an edge is a handle of its own,
# given up by a collection unless it is itself a root); there :meth:`Encoding.preimage`
# keeps to ``compose``.
STATIC_CORES = ("c", "python")
_CHECK_EVERY = 256  # nodes between two looks at the node table


def compose_by_levels(
    mgr,
    f: int,
    mapping: Mapping[int, int],
    keep: Iterable[int] | None = None,
    stats: dict | None = None,
) -> int:
    """``mgr.compose(f, mapping)``, computed one node of ``f`` at a time (see the module
    docstring). With ``keep`` (every edge the caller still needs that is not protected or
    held by a registered holder; ``f`` and the functions of ``mapping`` are kept in any
    case), garbage may be collected between two nodes (:meth:`BDD.maybe_gc`); without it
    nothing is collected and only the order of the work differs from ``compose``.

    ``stats``, when given, receives ``nodes`` (nodes of ``f`` substituted into) and ``held``
    (the largest number of sub-results alive at once)."""
    if getattr(mgr, "core", "python") not in STATIC_CORES:
        raise ValueError(f"compose_by_levels needs a core with a static order, not {mgr.core!r}")
    if not mapping or f <= 1:
        return f
    top, low, high = mgr.top, mgr.low, mgr.high
    last = max(mapping)  # a node below every substituted variable is its own sub-result
    root = f & ~1
    if top(root) > last:
        return f

    # The nodes of f that are substituted into, by level: their edge and two children; and
    # for every such node but the root the number of parents not yet done.
    by_level: dict[int, tuple[array, array, array]] = {}
    waiting: dict[int, int] = {}
    below: set[int] = set()  # children seen that are not substituted into
    stack = [root]
    while stack:
        e = stack.pop()
        lo, hi = low(e), high(e)
        rows = by_level.get(top(e))
        if rows is None:
            rows = by_level[top(e)] = (array("Q"), array("Q"), array("Q"))
        rows[0].append(e)
        rows[1].append(lo)
        rows[2].append(hi)
        for c in (lo & ~1, hi & ~1):
            if c <= 1 or c in below:
                continue
            k = waiting.get(c)
            if k is not None:
                waiting[c] = k + 1
            elif top(c) > last:
                below.add(c)
            else:
                waiting[c] = 1
                stack.append(c)
    del below

    collect = keep is not None
    held = [f, *mapping.values(), *(keep or ())]
    done: dict[int, int] = {}  # node (as its regular edge) -> sub-result
    ite, var, get, sub = mgr.ITE, mgr.var, mapping.get, done.get
    count = most = 0
    for v in sorted(by_level, reverse=True):
        edges, los, his = by_level.pop(v)
        g = get(v)
        for e, lo, hi in zip(edges, los, his, strict=True):
            c0, c1 = lo & ~1, hi & ~1
            r0 = sub(c0)
            r0 = lo if r0 is None else r0 ^ (lo & 1)
            r1 = sub(c1)
            r1 = hi if r1 is None else r1 ^ (hi & 1)
            # an unsubstituted variable stands for itself (made anew: a collection frees it)
            done[e] = ite(var(v) if g is None else g, r1, r0)
            for c in (c0, c1):
                k = waiting.get(c)
                if k is not None:
                    if k == 1:
                        del waiting[c], done[c]
                    else:
                        waiting[c] = k - 1
            count += 1
            if count % _CHECK_EVERY == 0:
                if len(done) > most:
                    most = len(done)
                if collect:
                    mgr.maybe_gc(chain(done.values(), held))
    if stats is not None:
        stats["nodes"] = stats.get("nodes", 0) + count
        stats["held"] = max(stats.get("held", 0), most, len(done))
    return done[root] ^ (f & 1)
