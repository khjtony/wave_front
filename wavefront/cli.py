"""The ``wf`` command line (spec section 10).

Models are referenced as ``path/to/model.py:attr``; ``attr`` defaults to ``model`` and may
name a :class:`~wavefront.model.Model` or a function returning one. A dotted module name
(``package.module:attr``) is imported as such. Exit codes: 0 on success, 2 on
:class:`~wavefront.model.ModelError` (message on stderr; ``argparse`` also uses 2 for
usage errors), 1 when the model cannot be loaded or the exploration budget is exceeded.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import sys
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType

from .analysis import (
    distance_table,
    is_uniform,
    pivotal,
    relax_explicit,
    run_all,
    strategy_closure,
    viability,
)
from .analysis._common import check_ending, complement, nearest_source, rest_of
from .engine import BudgetExceeded, Graph, attractor, contested, explore, witness
from .model import Model, ModelError
from .model.compile import CompiledModel
from .model.compile import compile as compile_model
from .report import CAVEAT, render

__all__ = ["main", "load_model", "ModelLoadError"]


class ModelLoadError(RuntimeError):
    """The model reference could not be resolved to a :class:`Model`."""


# -- loading ---------------------------------------------------------------------------


def _import_file(path: Path) -> ModuleType:
    path = path.resolve()
    if not path.is_file():
        raise ModelLoadError(f"model file {str(path)!r} does not exist")
    parts = [path.stem]
    root = path.parent
    while (root / "__init__.py").is_file():
        parts.insert(0, root.name)
        root = root.parent
    if len(parts) > 1:
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        module = importlib.import_module(".".join(parts))
        if module.__file__ and Path(module.__file__).resolve() == path:
            return module
    name = "_wf_model_" + hashlib.sha1(str(path).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ModelLoadError(f"cannot import {str(path)!r}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    added = str(path.parent) not in sys.path
    if added:
        sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    finally:
        if added:
            sys.path.remove(str(path.parent))
    return module


def load_model(ref: str) -> Model:
    """Resolve ``path/to/model.py[:attr]`` or ``package.module[:attr]`` to a
    :class:`Model` (``attr`` defaults to ``model``; a callable is called with no
    arguments)."""
    target, sep, attr = ref.rpartition(":")
    if not sep:
        target, attr = ref, ""
    attr = attr or "model"
    path = Path(target)
    if path.suffix == ".py" or path.exists():
        module = _import_file(path)
    else:
        try:
            module = importlib.import_module(target)
        except ImportError as exc:
            raise ModelLoadError(f"cannot import model module {target!r}: {exc}") from exc
    if not hasattr(module, attr):
        raise ModelLoadError(f"{target!r} has no attribute {attr!r}")
    obj = getattr(module, attr)
    if not isinstance(obj, Model) and callable(obj):
        obj = obj()
    if not isinstance(obj, Model):
        raise ModelLoadError(f"{ref!r} is a {type(obj).__name__}, not a wavefront Model")
    return obj


# -- helpers ---------------------------------------------------------------------------


def _names(text: str | None) -> list[str]:
    return [n.strip() for n in (text or "").split(",") if n.strip()]


def _profile(args: argparse.Namespace) -> str | list[str] | None:
    names = _names(args.profile)
    if not names:
        return None
    return names[0] if len(names) == 1 else names


def _compile(args: argparse.Namespace) -> tuple[Model, CompiledModel]:
    model = load_model(args.model)
    return model, compile_model(model, profile=_profile(args))


def _graph(args: argparse.Namespace, initial=None) -> tuple[Model, Graph]:
    model, cm = _compile(args)
    return model, explore(cm, initial=initial, max_states=args.max_states)


def _coalition(text: str) -> str:
    return "{" + ", ".join(_names(text)) + "}"


def _print_table(header: Sequence[str], rows: Sequence[Sequence[object]]) -> None:
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    for row in rows:
        print("| " + " | ".join(str(x) for x in row) + " |")


def _uniformity_line(g: Graph, coalition: list[str], strategy, sources, what: str) -> None:
    used = strategy_closure(g, coalition, strategy, sources)
    res = is_uniform(g, coalition, used)
    if res.uniform:
        print(f"The {what} strategy is uniform: each member can play it on its own observations.")
    else:
        member, s, t = res.conflicts[0]
        joint = "uniform" if res.jointly_uniform else "not uniform"
        print(
            f"Warning: the {what} strategy is not uniform per member ({len(res.conflicts)} "
            f"conflict(s), e.g. {member} cannot tell #{s} from #{t}; on pooled observations "
            f"it is {joint}); the result is an upper bound."
        )


# -- subcommands -----------------------------------------------------------------------


def cmd_explore(args: argparse.Namespace) -> int:
    model, g = _graph(args)
    endings: dict[str, int] = {}
    for e in g.ending:
        if e is not None:
            endings[e] = endings.get(e, 0) + 1
    print(f"model {model.name}: {g.size()} reachable states, {len(g.initial)} initial")
    print(f"terminal states: {sum(g.terminal)}")
    for name, count in endings.items():
        print(f"  {name}: {count}")
    print(f"max depth: {max(g.depth, default=0)}")
    print("parameter budget:")
    for key, value in g.model.budget().items():
        print(f"  {key}: {value}")
    return 0


def cmd_reach(args: argparse.Namespace) -> int:
    _, g = _graph(args)
    target = check_ending(g, args.ending)
    win = attractor(g, g.model.actor_names, target)
    hits = [s for s in g.initial if s in win.win]
    print(f"{args.ending}: reachable from {len(hits)} of {len(g.initial)} initial states.")
    print(f"Note: {CAVEAT}")
    source = nearest_source(g, g.initial, target)
    if source is not None:
        trace = witness(g, source, target)
        assert trace is not None
        print(f"Shortest witness: {len(trace) - 1} steps from initial state #{source}.")
        if args.trace:
            print()
            print(trace.render(g))
    return 0


def cmd_force(args: argparse.Namespace) -> int:
    _, g = _graph(args)
    coalition = _names(args.coalition)
    target = check_ending(g, args.ending)
    res = contested(g, coalition, target, "reach")
    att = attractor(g, coalition, target)
    rows = []
    for s in g.initial:
        status = "forced" if s in res.forced else "blocked" if s in res.blocked else "contested"
        rows.append((f"#{s}", status, att.rank.get(s, "-"), g.format_state(s)))
    print(f"Can {_coalition(args.coalition)} force {args.ending}?")
    _print_table(["initial state", "status", "forced within", "state"], rows)
    forced = [s for s in g.initial if s in res.forced]
    if forced:
        _uniformity_line(g, coalition, att.strategy, forced, "forcing")
    return 0


def cmd_viable(args: argparse.Namespace) -> int:
    initial = None
    if args.snapshot:
        try:
            from .evidence import load_snapshot
        except ImportError as exc:
            print(
                f"error: --snapshot needs wavefront.evidence, which is not available ({exc})",
                file=sys.stderr,
            )
            return 1
        model, cm = _compile(args)
        initial = [tuple(load_snapshot(args.snapshot, cm))]
        g = explore(cm, initial=initial, max_states=args.max_states)
    else:
        model, g = _graph(args)
    coalition = _names(args.coalition)
    k = viability(g, coalition, args.invariant)
    dist = distance_table(g, g.initial, k.kernel, coalition, None)
    members = [g.model.actors[i].name for i in g.actor_indices(coalition)]
    defect = {}
    if len(members) > 1:
        outside = complement(g, k.kernel)
        for m in members:
            defect[m] = attractor(g, [*rest_of(g, members), m], outside).rank
    print(f"Kernel of {_coalition(args.coalition)} for {args.invariant}: {len(k.kernel)} states")
    header = ["initial state", "in kernel", "shortest", "margin"]
    header += [f"forced if {m} defects" for m in defect]
    rows = []
    for s in g.initial:
        d = dist[s]
        row = [f"#{s}", "yes" if s in k.kernel else "no", d.shortest, d.margin]
        row += [defect[m].get(s) for m in defect]
        rows.append(["-" if x is None else x for x in row])
    _print_table(header, rows)
    kept = [s for s in g.initial if s in k.kernel]
    if kept:
        _uniformity_line(g, coalition, k.strategy, kept, "keeping")
    return 0


def cmd_mine(args: argparse.Namespace) -> int:
    model = load_model(args.model)
    profile = _profile(args)
    coalition = _names(args.coalition) or None
    if args.bmc:
        if coalition is not None:
            print("error: --bmc answers reachability only; drop --coalition", file=sys.stderr)
            return 1
        try:
            from . import bmc
        except ImportError as exc:
            print(f"error: --bmc needs wavefront.bmc and z3 ({exc})", file=sys.stderr)
            return 1
        cm = compile_model(model, profile=profile)
        k = args.k if args.k is not None else model.horizon
        if k is None:
            print("error: an untimed model needs --k with --bmc", file=sys.stderr)
            return 1
        res = bmc.relax(cm, k, args.ending, max_relax=args.max_relax)
        print(f"Minimal relaxation sets for {args.ending} (bounded, k = {k}):")
        sets = getattr(res, "minimal_sets", [])
        for s in sets:
            print("  {" + ", ".join(s) + "}")
        if not sets:
            print(f"  none of size at most {args.max_relax}")
        core = getattr(res, "core", [])
        if core:
            print("Blocking set (unsat core, not necessarily minimal): " + ", ".join(core))
        return 0
    if args.k is not None:
        print("note: --k applies to --bmc only; the explicit search covers the full horizon")
    sets = relax_explicit(
        model,
        args.ending,
        max_size=args.max_relax,
        coalition=coalition,
        profile=profile,
        max_states=args.max_states,
    )
    goal = "reach" if coalition is None else f"{_coalition(args.coalition)} to force"
    print(f"Minimal relaxation sets for {goal} {args.ending} (explicit, full horizon):")
    for s in sets:
        print("  {" + ", ".join(s) + "}")
    if not sets:
        print(f"  none of size at most {sets.max_size}")
    for s, msg in sets.ill_formed:
        print("ill-formed: {" + ", ".join(s) + "}: " + msg)
    for s, msg in sets.undecided:
        print("undecided: {" + ", ".join(s) + "}: " + msg)
    return 0


def cmd_pivot(args: argparse.Namespace) -> int:
    _, g = _graph(args)
    res = pivotal(g, args.ending, include_nature=args.nature)
    order = {n: i for i, n in enumerate(g.model.actor_names)}

    def fmt(cs: list[frozenset[str]]) -> str:
        if not cs:
            return "none"
        return "; ".join("{" + ", ".join(sorted(c, key=order.__getitem__)) + "}" for c in cs)

    print(f"Pivotal coalitions for {args.ending} (from every initial state):")
    print(f"  forcing:  {fmt(res.forcing)}")
    print(f"  blocking: {fmt(res.blocking)}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    model = load_model(args.model)
    coalitions = [_names(c) for c in args.coalition] if args.coalition else None
    analysis = run_all(
        model,
        coalitions=coalitions,
        profile=_profile(args),
        max_relax=args.max_relax,
        max_states=args.max_states,
    )
    text = render(analysis)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"report written to {args.out}")
    else:
        sys.stdout.write(text)
    return 0


# -- parser ----------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """The ``wf`` argument parser."""
    parser = argparse.ArgumentParser(
        prog="wf", description="Analyse finite concurrent games between strategic actors."
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    def command(name: str, func, help_text: str) -> argparse.ArgumentParser:
        p = sub.add_parser(name, help=help_text, description=help_text)
        p.add_argument("model", metavar="MODEL", help="path/to/model.py[:attr] (attr: model)")
        p.add_argument("--profile", help="behavioral profile(s) to select, comma-separated")
        p.add_argument("--max-states", type=int, default=1_000_000, help="exploration budget")
        p.set_defaults(func=func)
        return p

    command("explore", cmd_explore, "Explore the model and print its size and budget.")

    p = command("reach", cmd_reach, "Plain reachability of an ending (not a finding).")
    p.add_argument("--ending", required=True)
    p.add_argument("--trace", action="store_true", help="print the shortest witness trace")

    p = command("force", cmd_force, "Whether a coalition can force an ending.")
    p.add_argument("--coalition", required=True, help="actor names, comma-separated")
    p.add_argument("--ending", required=True)

    p = command("viable", cmd_viable, "Kernel membership and distances for an invariant.")
    p.add_argument("--coalition", required=True, help="actor names, comma-separated")
    p.add_argument("--invariant", required=True)
    p.add_argument("--snapshot", help="start from a snapshot file (wavefront.evidence)")

    p = command("mine", cmd_mine, "Minimal relaxation sets for an ending.")
    p.add_argument("--ending", required=True)
    p.add_argument("--k", type=int, help="bound for --bmc (default: the horizon)")
    p.add_argument("--max-relax", type=int, default=2, help="largest set size searched")
    p.add_argument("--coalition", help="ask for forceability by these actors (explicit only)")
    p.add_argument("--bmc", action="store_true", help="use the bounded model checker (z3)")

    p = command("pivot", cmd_pivot, "Minimal coalitions that force or block an ending.")
    p.add_argument("--ending", required=True)
    p.add_argument("--nature", action="store_true", help="let Nature join coalitions")

    p = command("report", cmd_report, "Full Markdown report.")
    p.add_argument("--out", help="write the report to this file instead of stdout")
    p.add_argument("--max-relax", type=int, default=2, help="largest relaxation set size")
    p.add_argument(
        "--coalition",
        action="append",
        help="coalition to analyse (comma-separated; repeatable; default: each actor and all)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run ``wf`` with ``argv`` (default ``sys.argv[1:]``) and return the exit code."""
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ModelError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (ModelLoadError, BudgetExceeded) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
