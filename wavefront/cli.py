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


def _parse_fix(text: str) -> tuple[str, str]:
    """``VAR=LEVEL`` for ``--fix``."""
    name, sep, level = text.partition("=")
    name, level = name.strip(), level.strip()
    if not sep or not name or not level:
        raise argparse.ArgumentTypeError(f"expected VAR=LEVEL, not {text!r}")
    return name, level


def _no_fix_without_snapshot(args: argparse.Namespace) -> None:
    if getattr(args, "fix", None):
        raise ModelError("--fix needs --snapshot: it fixes swept variables the snapshot omits")


def _snapshot_with_fixes(args: argparse.Namespace, model: Model) -> str | dict:
    """The ``--snapshot`` argument, or, with ``--fix VAR=LEVEL``, the parsed snapshot with
    each fixed variable added as an ``assumed`` entry. Only a swept variable (declared with
    ``init=None``) that the snapshot omits may be fixed; the level is checked when the
    snapshot is mapped onto the model."""
    fixes = getattr(args, "fix", None) or []
    if not fixes:
        return args.snapshot
    from .evidence import read_snapshot

    data = read_snapshot(args.snapshot)
    declared = {getattr(v, "name", None): v for v in model.variables}
    seen: set[str] = set()
    for name, level in fixes:
        decl = declared.get(name)
        if decl is None or not hasattr(decl, "kind"):
            raise ModelError(f"--fix {name}={level}: {name!r} is not a variable of the model")
        if decl.init is not None:
            raise ModelError(
                f"--fix {name}={level}: {name!r} is not swept (it has a declared initial value)"
            )
        if name in data["variables"] or name in seen:
            raise ModelError(f"--fix {name}={level}: the snapshot already fixes {name!r}")
        seen.add(name)
        if decl.kind == "flag":
            value: object = {"true": True, "false": False}.get(level.lower(), level)
        elif decl.kind == "counter":
            value = int(level) if level.isdigit() else level
        else:
            value = level
        data["variables"][name] = {"level": value, "confidence": "assumed", "indicators": []}
    return data


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


def _snapshot_members(args: argparse.Namespace, model: Model, cm):
    """The member states of ``--snapshot`` (with ``--fix``): one state, or the product set
    of a snapshot giving a set of levels (docs/ambiguous_levels.md)."""
    from .evidence import load_snapshot_states, snapshot_to_states

    snapshot = _snapshot_with_fixes(args, model)
    if isinstance(snapshot, dict):
        return snapshot_to_states(snapshot, cm)
    return load_snapshot_states(snapshot, cm)


def _print_robustness(results, show=str) -> None:
    """One line per robust/fragile verdict, after the member list."""
    if not results:
        return
    labels = results[0].labels
    print(f"Start state: a set of {len(labels)} member states (a snapshot with a set of levels):")
    for i, label in enumerate(labels):
        print(f"  member {i}: {label}")
    for r in results:
        print(f"{r.question}: {r.summary(show)}")


def cmd_viable(args: argparse.Namespace) -> int:
    initial = None
    snap_states = None
    if args.snapshot:
        try:
            from .evidence import load_snapshot_states  # noqa: F401
        except ImportError as exc:
            print(
                f"error: --snapshot needs wavefront.evidence, which is not available ({exc})",
                file=sys.stderr,
            )
            return 1
        model, cm = _compile(args)
        snap_states = _snapshot_members(args, model, cm)
        initial = list(snap_states.states)
        g = explore(cm, initial=initial, max_states=args.max_states)
    else:
        _no_fix_without_snapshot(args)
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
    if snap_states is not None and snap_states.is_set:
        from .analysis import robust_kernel

        rk = robust_kernel(g, snap_states, coalition, args.invariant)

        def show(x) -> str:
            if isinstance(x, bool):
                return "yes" if x else "no"
            return f"shortest {'-' if x.shortest is None else x.shortest}"

        _print_robustness([rk.in_kernel, rk.distance], show)
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


def cmd_viz(args: argparse.Namespace) -> int:
    from .viz import PageTooLarge, bundle, render_html

    model = load_model(args.model)
    coalitions = [_names(c) for c in args.coalition] if args.coalition else None
    endings = [e for text in args.ending for e in _names(text)] if args.ending else None
    snapshot = _snapshot_with_fixes(args, model) if args.snapshot else None
    if not args.snapshot:
        _no_fix_without_snapshot(args)
    try:
        data = bundle(
            model,
            coalitions=coalitions,
            endings=endings,
            profile=_profile(args),
            snapshot=snapshot,
            max_states=args.max_states,
            max_moves=args.max_moves,
            max_relax=args.max_relax,
        )
        out = render_html(data, args.out)
    except PageTooLarge as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    counts = data["meta"]["counts"]
    scope = "all" if data["moves"]["complete"] else "the shown traces' neighborhood of"
    print(
        f"page written to {out} ({out.stat().st_size / 1e6:.1f} MB; {counts['states']} states, "
        f"{scope} {counts['moves']} joint moves)"
    )
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    model = load_model(args.model)
    coalitions = [_names(c) for c in args.coalition] if args.coalition else None
    initial = members = None
    if args.snapshot:
        found = _snapshot_members(args, model, compile_model(model, profile=_profile(args)))
        if found.is_set:
            members = found
        else:
            initial = list(found.states)
    else:
        _no_fix_without_snapshot(args)
    analysis = run_all(
        model,
        coalitions=coalitions,
        initial=initial,
        members=members,
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


# -- evidence: extraction, review and replay (ww2_testbed.md section 8) -----------------


def _evidence_errors():
    from .evidence.corpora import CorpusError
    from .evidence.extract import ExtractError, ProposalsFileError
    from .evidence.replay import ReplayError
    from .evidence.review import ReviewError

    return (CorpusError, ExtractError, ProposalsFileError, ReplayError, ReviewError, ValueError)


def _date_arg(text: str):
    from datetime import date

    try:
        return date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not a date in YYYY-MM-DD form") from None


def _evidence(func):
    """Run an evidence subcommand; its user errors exit 2 with the message on stderr, and a
    missing optional SDK or a backend error that reaches here (an ``ExtractError``) exits 1.
    ``wf extract`` also exits 1 when the backend failed on a document (the error is recorded
    and the proposals file still written); ``wf replay`` turns such a failure into a
    ``ReplayError``, so it exits 2 without writing the period's proposals file."""

    def run(args: argparse.Namespace) -> int:
        from .evidence.extract import ExtractError

        try:
            return func(args)
        except ExtractError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        except _evidence_errors() as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    return run


def _shown(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


@_evidence
def cmd_extract(args: argparse.Namespace) -> int:
    from .evidence.corpora import open_corpus
    from .evidence.extract import (
        CachedBackend,
        extract,
        make_backend,
        text_variables,
        write_proposals,
    )
    from .evidence.harness_rules import parse_rules
    from .evidence.replay import backend_info
    from .evidence.review import label_for

    rules = parse_rules(args.rules)
    episode = None if args.episode == "ww2" else args.episode
    corpus = open_corpus(args.corpus, args.source)
    backend = make_backend(args.backend, args.model, _guidance(args))
    if args.cache:
        backend = CachedBackend(backend, args.cache)
    result = extract(
        corpus,
        until=args.until,
        since=args.since,
        backend=backend,
        workers=args.workers,
        variables=text_variables(episode=args.episode),
    )
    info = backend_info(backend)
    usage = getattr(backend, "usage", None)
    if usage:
        info["usage"] = dict(usage)
    data = write_proposals(
        args.out,
        result,
        label=label_for(args.until, episode),
        corpus=corpus.describe(),
        backend=info,
        harness_rules=rules,
        episode=episode,
    )
    print(
        f"{len(result.documents)} documents dated to {args.until} read; "
        f"{len(data['proposals'])} proposals written to {args.out} "
        f"({len(result.discarded)} discarded by the checks, {len(result.errors)} backend errors)"
    )
    if usage:
        print("tokens: " + ", ".join(f"{k} {v}" for k, v in sorted(usage.items())))
    if corpus.synthetic:
        print("note: the corpus is a SYNTHETIC fixture; its proposals are not evidence")
    for err in result.errors:
        print(f"error: {err['document']}: {err['error']}", file=sys.stderr)
    return 1 if result.errors else 0


@_evidence
def cmd_review(args: argparse.Namespace) -> int:
    import getpass

    from .evidence.extract import read_proposals
    from .evidence.review import decide, file_gates, format_listing

    if args.accept or args.reject:
        status, ids = ("accepted", args.accept) if args.accept else ("rejected", args.reject)
        reviewer = args.reviewer or getpass.getuser()
        written = decide(
            args.proposals,
            ids,
            status,
            note=args.note or "",
            reviewer=reviewer,
            snapshots_dir=args.snapshots,
            hindsight_dir=args.hindsight,
        )
        print(f"{status}: {ids}")
        for path in written:
            print(f"replay snapshot written: {_shown(path)}")
        if not written:
            print("no replay snapshot written: proposals up to this date are still pending")
        return 0
    data = read_proposals(args.proposals)
    print(format_listing(data, file_gates(args.proposals)))
    return 0


def _guidance(args: argparse.Namespace) -> str | None:
    """The text of ``--guidance-file`` (an empty file: no guidance), or None (the default)."""
    path = getattr(args, "guidance_file", None)
    if not path:
        return None
    if args.backend != "deepseek":
        raise SystemExit("error: --guidance-file applies to the deepseek backend only")
    return Path(path).read_text(encoding="utf-8")


def _print_plan(rows, backend, episode: str = "ww2") -> None:
    from .evidence.extract import text_variables
    from .evidence.extract.claude_backend import system_prompt
    from .evidence.extract.deepseek_backend import deepseek_system_prompt
    from .evidence.replay import CHARS_PER_TOKEN

    prompts = {"claude": system_prompt, "deepseek": deepseek_system_prompt}
    prompt = prompts.get(backend.name)
    system_chars = len(prompt(text_variables(episode=episode))) if prompt else 0
    print("DRY RUN: nothing is sent to the backend and nothing is written")
    print(
        f"{'quarter' if episode == 'ww2' else 'year':8} {'visible':>8} {'to read':>8} "
        f"{'cached':>7} {'requests':>9} {'characters':>11}"
    )
    for r in rows:
        print(
            f"{r.quarter:8} {r.visible:8d} {r.to_read:8d} {r.cached:7d} {r.requests:9d} "
            f"{r.characters:11d}"
        )
    requests = sum(r.requests for r in rows)
    chars = sum(r.characters for r in rows)
    print(
        f"total: {sum(r.to_read for r in rows)} documents to read, "
        f"{sum(r.cached for r in rows)} of them cached, {requests} requests, "
        f"{chars} characters of document text"
    )
    if system_chars:
        per_request = system_chars + 400  # the system prompt and the document header
        text_tokens = chars // CHARS_PER_TOKEN
        prompt_tokens = requests * per_request // CHARS_PER_TOKEN
        print(
            f"input tokens, estimated at {CHARS_PER_TOKEN} characters a token: about "
            f"{text_tokens + prompt_tokens} ({text_tokens} of document text, {prompt_tokens} of "
            f"system prompt and headers, of which the {system_chars // CHARS_PER_TOKEN}-token "
            "system prompt is cacheable); output tokens (thinking and the JSON answer) are "
            "not estimated: measure them on a pilot quarter (the proposals file records usage)"
        )


@_evidence
def cmd_replay(args: argparse.Namespace) -> int:
    from .evidence.corpora import open_corpus
    from .evidence.episodes import get_episode
    from .evidence.extract import make_backend
    from .evidence.harness_rules import parse_rules
    from .evidence.replay import (
        backend_info,
        compare,
        parse_quarters,
        plan,
        render_report,
        replay,
    )
    from .evidence.review import DEFAULT_HINDSIGHT

    ep = get_episode(args.episode)
    if ep.name == "ww2":
        if args.years:
            raise ValueError("--years is for --episode cw; the WW2 replay runs by --quarters")
        periods_text = args.quarters or "1936Q1..1940Q4"
        quarters = parse_quarters(periods_text)
    else:
        if args.quarters:
            raise ValueError(
                f"--episode {ep.name} runs by year (the model ticks yearly): give --years, "
                "e.g. --years 1957..1962"
            )
        if not args.years:
            raise ValueError(f"--episode {ep.name} needs --years, e.g. --years 1957..1962")
        periods_text = args.years
        quarters = ep.parse_periods(periods_text)
    out = Path(args.out)
    runs = []
    rules = parse_rules(args.rules) if args.rules is not None else None
    if args.drop_rejected and (not args.measure_proposals or args.corpus or ep.name != "ww2"):
        raise ValueError(
            "--drop-rejected goes with --measure-proposals on proposals already written "
            "(no --corpus), WW2 only"
        )
    if args.measure_proposals and (args.auto_accept or args.metrics_only):
        raise ValueError("--measure-proposals goes with neither --auto-accept nor --metrics-only")
    if args.dry_run and (args.auto_accept or args.metrics_only or args.measure_proposals):
        raise ValueError(
            "--dry-run goes with none of --auto-accept, --metrics-only, --measure-proposals"
        )
    if args.metrics_only and rules is not None:
        raise ValueError(
            "--rules does not go with --metrics-only: the reviewed snapshots were built under the "
            "rules recorded in the proposals files"
        )
    if args.dry_run:
        if not args.corpus:
            raise ValueError("--dry-run needs --corpus")
        corpus = open_corpus(args.corpus, args.source)
        backend = make_backend(args.backend, args.model, _guidance(args))
        _print_plan(plan(corpus, quarters, out, backend, episode=ep), backend, ep.name)
        return 0
    if args.measure_proposals and not args.corpus:
        from .evidence.review import proposal_files

        files = proposal_files(out / "proposals")
        if not files:
            raise ValueError(f"{out / 'proposals'}: no proposals files to measure")
        corpus_info = files[0][1]["corpus"]
        backend_record = files[0][1].get("backend", {"name": "(unknown)"})
    elif args.metrics_only:
        corpus_info = {"source": "(metrics only)", "synthetic": False}
        backend_record = {"name": "(metrics only)"}
    else:
        if not args.corpus:
            raise ValueError("--corpus is required unless --metrics-only")
        corpus = open_corpus(args.corpus, args.source)
        backend = make_backend(args.backend, args.model, _guidance(args))
        runs = replay(
            corpus,
            quarters,
            out,
            backend,
            auto_accept=args.auto_accept,
            hindsight_dir=args.hindsight,
            rules=parse_rules(args.rules),
            workers=args.workers,
            cache=not args.no_cache,
            episode=ep,
        )
        corpus_info = corpus.describe()
        backend_record = backend_info(backend)
        if corpus.synthetic:
            print("SYNTHETIC RUN: fixture corpus; the results are not evidence")
        if args.auto_accept:
            print("AUTO-ACCEPT: every proposal accepted without review (synthetic run only)")
    if ep.name == "ww2":
        metrics = compare(
            out,
            quarters,
            args.hindsight or DEFAULT_HINDSIGHT,
            measure_proposals=args.measure_proposals,
            rules=rules,
            drop_rejected=args.drop_rejected,
        )
        command = f"wf replay --quarters {periods_text} --out OUT"
    else:
        from .evidence.replay_cw import compare as compare_cw

        metrics = compare_cw(
            out, quarters, args.hindsight, measure_proposals=args.measure_proposals, rules=rules
        )
        command = f"wf replay --episode {ep.name} --years {periods_text} --out OUT"
    if args.corpus:
        command += f" --corpus {_shown(Path(args.corpus))}"
    if args.backend != "rules":
        command += f" --backend {args.backend}"
    if args.model:
        command += f" --model {args.model}"
    if args.guidance_file and args.corpus:
        command += f" --guidance-file {_shown(Path(args.guidance_file))}"
    if args.rules is not None:
        command += f" --rules {args.rules}"
    if args.auto_accept:
        command += " --auto-accept"
    if args.metrics_only:
        command += " --metrics-only"
    if args.measure_proposals:
        command += " --measure-proposals"
    if args.drop_rejected:
        command += " --drop-rejected"
    if args.measure_proposals and args.drop_rejected:
        print(
            "PROPOSAL-LEVEL: rejected proposals left out, the accepted and the pending ones "
            "treated as accepted for the metrics; nothing written"
        )
    elif args.measure_proposals:
        print("PROPOSAL-LEVEL: every proposal treated as accepted for the metrics; nothing written")
    text = render_report(
        metrics,
        title=args.title or f"Replay metrics, {ep.title} {quarters[0]} to {quarters[-1]}",
        corpus=corpus_info,
        backend=backend_record,
        command=command,
        runs=runs,
    )
    report = Path(args.report) if args.report else out / "metrics.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(text, encoding="utf-8")
    for r in runs:
        snap = "snapshot" if r.snapshot else "proposals awaiting review"
        print(
            f"{r.quarter}: {r.visible} documents visible, {r.read} read, "
            f"{r.proposals} proposals ({snap})"
        )
    print(f"harness rules: {', '.join(metrics.rules) if metrics.rules else 'none'}")
    print(f"metrics report written to {_shown(report)}")
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
    p.add_argument(
        "--fix",
        action="append",
        type=_parse_fix,
        metavar="VAR=LEVEL",
        help="fix a swept variable the snapshot omits (repeatable; needs --snapshot)",
    )

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
    p.add_argument(
        "--snapshot",
        help="start from a snapshot file (wavefront.evidence); with a set of levels the "
        "report adds the robust/fragile verdicts",
    )
    p.add_argument(
        "--fix",
        action="append",
        type=_parse_fix,
        metavar="VAR=LEVEL",
        help="fix a swept variable the snapshot omits (repeatable; needs --snapshot)",
    )
    p.add_argument("--max-relax", type=int, default=2, help="largest relaxation set size")
    p.add_argument(
        "--coalition",
        action="append",
        help="coalition to analyse (comma-separated; repeatable; default: each actor and all)",
    )
    p = command("viz", cmd_viz, "Self-contained HTML visualizer page.")
    p.add_argument("--out", required=True, help="the HTML file to write")
    p.add_argument("--snapshot", help="start from a snapshot file (wavefront.evidence)")
    p.add_argument(
        "--fix",
        action="append",
        type=_parse_fix,
        metavar="VAR=LEVEL",
        help="fix a swept variable the snapshot omits (repeatable; needs --snapshot)",
    )
    p.add_argument(
        "--coalition",
        action="append",
        help="coalition to analyse (comma-separated; repeatable; default: each actor and all)",
    )
    p.add_argument(
        "--ending",
        action="append",
        help="ending to offer, the first one selected (repeatable; default: every ending)",
    )
    p.add_argument(
        "--max-moves",
        type=int,
        default=1_500_000,
        help="include the full move table up to this many joint moves (default 1,500,000)",
    )
    p.add_argument("--max-relax", type=int, default=2, help="largest relaxation set size")
    _add_evidence_commands(sub)
    return parser


def _add_evidence_commands(sub) -> None:
    """``extract``, ``review`` and ``replay``: the evidence pipeline of the replay harness."""
    p = sub.add_parser(
        "extract",
        help="Propose levels from the documents of a corpus up to a date.",
        description="Run an extraction backend over the documents of CORPUS dated at or "
        "before --until and write a proposals file for review. Nothing changes a snapshot.",
    )
    p.add_argument("corpus", metavar="CORPUS", help="corpus directory (index.json or .txt files)")
    p.add_argument("--until", type=_date_arg, required=True, help="last document date, YYYY-MM-DD")
    p.add_argument("--since", type=_date_arg, help="first document date, YYYY-MM-DD")
    p.add_argument("--out", required=True, metavar="PROPOSALS", help="proposals file to write")
    p.add_argument("--source", help="corpus kind (local, frus, hansard, chronicling, trove, crest)")
    p.add_argument(
        "--episode",
        choices=("ww2", "cw"),
        default="ww2",
        help="the model whose text variables are proposed: ww2 (default) or cw (the Cold War)",
    )
    p.add_argument("--backend", choices=("rules", "claude", "deepseek"), default="rules")
    p.add_argument(
        "--model", help="model for the claude or deepseek backend (default: the backend's)"
    )
    p.add_argument(
        "--guidance-file",
        help="deepseek backend: a text file of instructions replacing the default guidance "
        "(an empty file: no guidance); its SHA-256 is recorded in the proposals file",
    )
    p.add_argument(
        "--rules",
        metavar="RULES",
        help="harness rules recorded in the proposals file, comma-separated: two-document, "
        "no-retrospective, or none (default: both)",
    )
    p.add_argument(
        "--workers",
        type=int,
        default=1,
        help="documents read at a time by the backend (default 1)",
    )
    p.add_argument(
        "--cache",
        metavar="DIR",
        help="cache each document's answer in DIR; a second run reads cached documents from it",
    )
    p.set_defaults(func=cmd_extract)

    p = sub.add_parser(
        "review",
        help="List, accept or reject proposals; only accepted ones become snapshot levels.",
        description="List the proposals of a file, or accept or reject some with a note. "
        "After each decision the replay snapshots are rebuilt from accepted proposals only.",
    )
    p.add_argument("proposals", metavar="PROPOSALS", help="proposals file")
    action = p.add_mutually_exclusive_group()
    action.add_argument("--list", action="store_true", help="list the proposals (default)")
    action.add_argument("--accept", metavar="IDS", help="proposal ids to accept, comma-separated")
    action.add_argument("--reject", metavar="IDS", help="proposal ids to reject, comma-separated")
    p.add_argument("--note", help="the reviewer's note (required to accept or reject)")
    p.add_argument("--reviewer", help="reviewer name (default: the login name)")
    p.add_argument("--snapshots", help="snapshot directory (default: the parent of proposals/)")
    p.add_argument(
        "--hindsight",
        help="hindsight snapshots the resource variables (Cold War: every variable but the "
        "beliefs) are copied from (default: the proposals' episode's, snapshots/ww2/hindsight "
        "or snapshots/cw_v1/hindsight)",
    )
    p.set_defaults(func=cmd_review)

    p = sub.add_parser(
        "replay",
        help="Blind replay over quarters (WW2) or years (Cold War), with the metrics.",
        description="For each quarter, filter the corpus to documents dated at or before its "
        "end, extract and write proposals; then compare the reviewed replay snapshots with "
        "the hindsight snapshots and write a Markdown metrics report.",
    )
    p.add_argument("--corpus", help="corpus directory")
    p.add_argument(
        "--episode",
        choices=("ww2", "cw"),
        default="ww2",
        help="ww2 (default; by quarter) or cw (the Cold War; by year, with --years)",
    )
    p.add_argument("--quarters", help="WW2 quarters (default 1936Q1..1940Q4)")
    p.add_argument(
        "--years",
        help="Cold War years, e.g. 1957..1962: the snapshot of a year is its 1 January, read "
        "from the documents dated to the 31 December before",
    )
    p.add_argument("--out", required=True, help="replay directory (proposals/ and snapshots)")
    p.add_argument(
        "--auto-accept",
        action="store_true",
        help="accept every proposal without review (synthetic fixture corpus only; flagged)",
    )
    p.add_argument("--source", help="corpus kind (local, frus, hansard, chronicling, trove, crest)")
    p.add_argument("--backend", choices=("rules", "claude", "deepseek"), default="rules")
    p.add_argument(
        "--model", help="model for the claude or deepseek backend (default: the backend's)"
    )
    p.add_argument(
        "--guidance-file",
        help="deepseek backend: a text file of instructions replacing the default guidance "
        "(an empty file: no guidance); its SHA-256 is recorded in the proposals file",
    )
    p.add_argument(
        "--hindsight",
        help="hindsight snapshots to compare with (default: the episode's, snapshots/ww2/"
        "hindsight or snapshots/cw_v1/hindsight)",
    )
    p.add_argument("--report", help="metrics report file (default: OUT/metrics.md)")
    p.add_argument("--title", help="report title")
    p.add_argument(
        "--metrics-only",
        action="store_true",
        help="only recompute the metrics from the snapshots already in --out",
    )
    p.add_argument(
        "--measure-proposals",
        action="store_true",
        help="compute the metrics from the proposals in OUT/proposals as if every one were "
        "accepted, without review and without writing snapshots (a measurement of the "
        "backend; the report says so); with --corpus the extraction runs first",
    )
    p.add_argument(
        "--drop-rejected",
        action="store_true",
        help="with --measure-proposals: leave out the proposals a reviewer rejected and treat "
        "the accepted and the pending ones as accepted (a partly reviewed run; WW2)",
    )
    p.add_argument(
        "--rules",
        metavar="RULES",
        help="harness rules, comma-separated: two-document, no-retrospective, or none. With "
        "--corpus they are recorded in the proposals files (default: both); with "
        "--measure-proposals alone they replace the recorded ones for the measurement",
    )
    p.add_argument(
        "--workers",
        type=int,
        default=1,
        help="documents read at a time by the backend (default 1)",
    )
    p.add_argument(
        "--no-cache",
        action="store_true",
        help="do not cache the answers of a paid backend under OUT/cache/<backend>/ (default: "
        "cached, so running the same command again resumes a stopped run)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="count the documents, requests and characters a run would send per quarter "
        "(skipping documents already read or cached) and stop; nothing is sent or written",
    )
    p.set_defaults(func=cmd_replay)


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
