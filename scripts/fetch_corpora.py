#!/usr/bin/env python3
"""Fetch the replay corpora into ``data/ww2/corpora/raw/<source>/`` (git-ignored) and index them.

Run on the owner's machine: the corpus hosts are blocked from the development environment
(docs/phase2_kickoff.md). Every downloaded file is recorded in ``<source>/MANIFEST.json`` with
its URL, fetch date, size and SHA-256, and ``<source>/index.json`` lists the admissible
documents (dated, with full text) found in them. ``--check`` validates the indexes against the
manifests and the files without the network. See data/ww2/corpora/README.md for what each
source provides and its terms of use.

Examples::

    python3 scripts/fetch_corpora.py frus --since 1936-01-01 --until 1940-12-31
    python3 scripts/fetch_corpora.py frus --volumes frus1939v01,frus1931-41v02
    python3 scripts/fetch_corpora.py hansard --since 1939-03-01 --until 1939-04-30
    python3 scripts/fetch_corpora.py chronicling --since 1939-03-01 --until 1939-03-31 \\
        --terms Hitler,Chamberlain,Danzig
    TROVE_API_KEY=... python3 scripts/fetch_corpora.py trove --since 1939-03-01 \\
        --until 1939-03-31 --terms Hitler,Czechoslovakia
    python3 scripts/fetch_corpora.py --check
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wavefront.evidence.corpora import (  # noqa: E402
    SOURCES,
    CorpusError,
    chronicling,
    default_fetcher,
    frus,
    hansard,
    trove,
)
from wavefront.evidence.corpora.base import RAW_ROOT  # noqa: E402

# Query terms for the 1936 to 1940 crises (the structural events of data/ww2/events_ww2.csv).
DEFAULT_TERMS = (
    "Germany",
    "Hitler",
    "Rhineland",
    "Locarno",
    "Austria",
    "Czechoslovakia",
    "Sudeten",
    "Munich",
    "Prague",
    "Poland",
    "Danzig",
    "guarantee",
    "conscription",
    "rearmament",
    "neutrality",
    "Soviet",
    "Molotov",
    "Ribbentrop",
    "Axis",
    "Anti-Comintern",
    "Rumania",
)
DEFAULT_SINCE = date(1936, 1, 1)
DEFAULT_UNTIL = date(1940, 12, 31)


def _date(text: str) -> date:
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not YYYY-MM-DD") from None


def _list(text: str) -> list[str]:
    return [t.strip() for t in text.split(",") if t.strip()]


def check(root: Path, sources: list[str]) -> int:
    status = 0
    for name in sources or list(SOURCES):
        corpus = SOURCES[name](root / name)
        if not corpus.index_path.exists():
            print(f"{name}: no index at {corpus.index_path} (not fetched)")
            continue
        problems = corpus.check()
        n = len(corpus.read_index()) if not problems else "?"
        if problems:
            status = 1
            print(f"{name}: {len(problems)} problem(s)")
            for p in problems:
                print(f"  {p}")
        else:
            print(f"{name}: index valid ({n} documents)")
    return status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=RAW_ROOT, help="raw corpus directory")
    parser.add_argument(
        "--check",
        nargs="*",
        metavar="SOURCE",
        help="validate the indexes (all sources, or those named) without the network",
    )
    sub = parser.add_subparsers(dest="source")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--since", type=_date, default=DEFAULT_SINCE)
    common.add_argument("--until", type=_date, default=DEFAULT_UNTIL)
    common.add_argument("--terms", type=_list, help="comma-separated query terms")
    common.add_argument("--delay", type=float, default=1.0, help="seconds between requests")

    p = sub.add_parser("frus", parents=[common], help="FRUS volumes (TEI XML)")
    p.add_argument("--volumes", type=_list, default=list(frus.DEFAULT_VOLUMES))
    p = sub.add_parser("hansard", parents=[common], help="Historic Hansard sitting days")
    p.add_argument("--houses", type=_list, default=["commons"])
    p = sub.add_parser("chronicling", parents=[common], help="Chronicling America pages")
    p.add_argument("--max-pages", type=int)
    p = sub.add_parser("trove", parents=[common], help="Trove newspaper articles")
    p.add_argument("--max-pages", type=int)
    p.add_argument("--key-env", default="TROVE_API_KEY", help="environment variable with the key")

    args = parser.parse_args(argv)
    if args.check is not None:
        return check(args.root, args.check)
    if not args.source:
        parser.error("name a source to fetch, or --check")
    fetcher = default_fetcher(delay=args.delay)
    corpus = SOURCES[args.source](args.root / args.source)
    try:
        if args.source == "frus":
            n, skipped = frus.fetch(
                corpus,
                args.volumes,
                since=args.since,
                until=args.until,
                terms=args.terms or (),
                fetcher=fetcher,
            )
        elif args.source == "hansard":
            n, skipped = hansard.fetch(
                corpus,
                since=args.since,
                until=args.until,
                terms=args.terms or (),
                houses=args.houses,
                fetcher=fetcher,
            )
        elif args.source == "chronicling":
            n, skipped = chronicling.fetch(
                corpus,
                since=args.since,
                until=args.until,
                terms=args.terms or DEFAULT_TERMS,
                fetcher=fetcher,
                max_pages=args.max_pages,
            )
        else:
            n, skipped = trove.fetch(
                corpus,
                since=args.since,
                until=args.until,
                terms=args.terms or DEFAULT_TERMS,
                api_key=os.environ.get(args.key_env, ""),
                fetcher=fetcher,
                max_pages=args.max_pages,
            )
    except CorpusError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"{args.source}: {n} documents indexed in {corpus.index_path}; {len(skipped)} skipped")
    return check(args.root, [args.source])


if __name__ == "__main__":
    raise SystemExit(main())
