"""Compare a backend's proposals with a reference run's on the same documents.

Reads the documents a reference proposals file lists (``--reference``, e.g. the Claude
backend's ``proposals/1936Q1.json``), takes ``--n`` of them from ``--offset`` in the file's
order, runs ``--backend`` on them through the extractor's checks with a per-document cache, and
compares the kept proposals with the reference's, per document, as (variable, level) pairs:

- match: same document, variable and level;
- level differs: same document and variable, another level;
- extra: proposed here, not in the reference; missing: in the reference, not here.

The reference is another reader, not the truth: agreement measures whether the two read the
documents alike. Writes ``<out>/<tag>.json`` (every proposal with its quote, the discards and
errors, the usage) and prints a summary. Example::

    python scripts/compare_backends.py --corpus data/ww2/corpora/raw/frus \\
        --reference ~/wf_runs/frus_claude/proposals/1936Q1.json --backend deepseek \\
        --n 200 --out ~/wf_runs/deepseek_eval --tag v0
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

from wavefront.evidence.corpora import open_corpus
from wavefront.evidence.extract import CachedBackend, extract, make_backend, text_variables
from wavefront.evidence.extract.deepseek_backend import DeepSeekBackend


def _pairs(records):
    out: dict[str, set[tuple[str, str]]] = {}
    for doc, var, level in records:
        out.setdefault(doc, set()).add((var, str(level)))
    return out


def compare(ours: dict, ref: dict, docs: list[str]) -> dict:
    counts = Counter()
    by_var: dict[str, Counter] = {}
    rows = []
    for d in docs:
        a, b = ours.get(d, set()), ref.get(d, set())
        a_vars, b_vars = {v for v, _ in a}, {v for v, _ in b}
        for v, lv in a | b:
            if (v, lv) in a and (v, lv) in b:
                kind = "match"
            elif v in a_vars and v in b_vars:
                kind = "level differs"
            elif (v, lv) in a:
                kind = "extra"
            else:
                kind = "missing"
            counts[kind] += 1
            by_var.setdefault(v, Counter())[kind] += 1
            if kind != "match":
                rows.append({"document": d, "variable": v, "level": lv, "kind": kind})
    # "level differs" is counted once per side; halve it to count variables, not pairs.
    n_ours = sum(len(ours.get(d, ())) for d in docs)
    n_ref = sum(len(ref.get(d, ())) for d in docs)
    return {
        "proposals": n_ours,
        "reference_proposals": n_ref,
        "counts": dict(counts),
        "precision": counts["match"] / n_ours if n_ours else None,
        "recall": counts["match"] / n_ref if n_ref else None,
        "by_variable": {v: dict(c) for v, c in sorted(by_var.items())},
        "disagreements": rows,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--corpus", required=True)
    p.add_argument("--reference", required=True)
    p.add_argument("--backend", default="deepseek")
    p.add_argument("--model")
    p.add_argument("--effort")
    p.add_argument("--guidance-file", help="extra instructions (deepseek backend)")
    p.add_argument("--n", type=int, default=200)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--out", required=True)
    p.add_argument("--tag", required=True)
    args = p.parse_args(argv)

    reference = json.loads(Path(args.reference).read_text(encoding="utf-8"))
    ids = [d["id"] for d in reference["documents"]][args.offset : args.offset + args.n]
    wanted = set(ids)
    until = max(date.fromisoformat(d["date"]) for d in reference["documents"])
    since = min(date.fromisoformat(d["date"]) for d in reference["documents"])
    corpus = open_corpus(args.corpus)
    docs = [d for d in corpus.iter_documents(until, since) if d.id in wanted]
    if len(docs) != len(ids):
        print(f"error: found {len(docs)} of {len(ids)} documents", file=sys.stderr)
        return 2

    if args.backend == "deepseek":
        kw = {}
        if args.model:
            kw["model"] = args.model
        if args.effort:
            kw["effort"] = args.effort
        if args.guidance_file:
            kw["guidance"] = Path(args.guidance_file).read_text(encoding="utf-8")
        backend = DeepSeekBackend(**kw)
    else:
        backend = make_backend(args.backend, args.model)
    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    cached = CachedBackend(backend, out / "cache" / backend.name)

    class Selected:
        synthetic = False

        def iter_documents(self, until, since=None):
            yield from docs

    result = extract(
        Selected(), until=until, backend=cached, variables=text_variables(), workers=args.workers
    )
    ours = _pairs((d.id, p.variable, p.level) for d, p in result.kept)
    ref = _pairs(
        (r["document"], r["proposal"]["variable"], r["proposal"]["level"])
        for r in reference["proposals"]
        if r["document"] in wanted
    )
    report = compare(ours, ref, ids)
    report |= {
        "tag": args.tag,
        "documents": len(ids),
        "offset": args.offset,
        "model": getattr(backend, "model", None),
        "effort": getattr(backend, "effort", None),
        "usage": dict(getattr(backend, "usage", {}) or {}),
        "requests": getattr(backend, "requests", None),
        "discarded": result.discarded,
        "errors": result.errors,
        "kept": [{"document": d.id, **p.to_json()} for d, p in result.kept],
    }
    (out / f"{args.tag}.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    c = report["counts"]
    print(
        f"[{args.tag}] {len(ids)} documents; ours {report['proposals']}, reference "
        f"{report['reference_proposals']}; match {c.get('match', 0)}, level differs "
        f"{c.get('level differs', 0)}, extra {c.get('extra', 0)}, missing {c.get('missing', 0)}; "
        f"precision {report['precision']}, recall {report['recall']}; discarded "
        f"{len(result.discarded)}, errors {len(result.errors)}; usage {report['usage']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
