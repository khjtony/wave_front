#!/usr/bin/env python3
"""Fetch the WW2 testbed's raw datasets into ``data/ww2/raw/`` and derive the committed extract.

Raw files are never committed (``data/ww2/raw/`` is git-ignored). Every download is recorded
in ``data/ww2/raw/MANIFEST.json`` with its URL, date, size and SHA-256, and the committed
extract ``data/ww2/nmc_1936_1940.csv`` names the source, version and checksum in its header.

Three ways to obtain the files:

``--mirror``
    The R data mirrors in the ``peacesciencer`` package on GitHub (``cow_nmc.rda``,
    ``cow_mid_disps.rda``). Use this where the official hosts are unreachable. Reading them
    needs the ``data`` extra (``pyreadr``).
``--official --nmc-url URL [--mid-url URL]``
    The official Correlates of War files. Download links change between releases, so the URL
    is not built in: copy it from the data set pages (printed by ``--official`` without a URL).
    A ``.zip`` is unpacked into the raw directory.
``--from-file nmc=PATH`` (repeatable)
    A file already on disk (for example downloaded by hand), copied into the raw directory
    and recorded in the manifest.

Then, unless ``--no-extract``, the NMC rows for the eight WW2 powers, 1933 to 1941, are written
to ``data/ww2/nmc_1936_1940.csv``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wavefront.evidence.datasets import mid, nmc  # noqa: E402

RAW_DIR = ROOT / "data" / "ww2" / "raw"
EXTRACT = ROOT / "data" / "ww2" / "nmc_1936_1940.csv"
MIRRORS = {"nmc": nmc.MIRROR_URL, "mid": mid.MIRROR_URL}
OFFICIAL_PAGES = {"nmc": nmc.OFFICIAL_PAGE, "mid": mid.OFFICIAL_PAGE}

# Germany, France, the United Kingdom, the USSR, Japan, Italy, the United States, Poland.
EXTRACT_CCODES = (255, 220, 200, 365, 740, 325, 2, 290)
EXTRACT_YEARS = range(1933, 1942)


def shown(path: Path) -> str:
    """``path`` relative to the repository when it is inside it."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 16), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, target: Path) -> Path:
    """Download ``url`` to ``target`` (via a temporary name, so a failed transfer leaves no
    partial file). Proxies and CA bundles come from the environment."""
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "wave_front data fetch"})
    with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as out:
        shutil.copyfileobj(response, out)
    partial.replace(target)
    return target


def record(manifest: dict, dataset: str, path: Path, origin: str, via: str) -> None:
    manifest[path.name] = {
        "dataset": dataset,
        "origin": origin,
        "obtained_via": via,
        "fetched": date.today().isoformat(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }
    print(f"{dataset}: {shown(path)} ({path.stat().st_size} bytes) from {origin}")


def unpack(path: Path, raw_dir: Path) -> list[Path]:
    """The CSV files inside a downloaded zip, extracted flat into ``raw_dir``."""
    if path.suffix.lower() != ".zip":
        return [path]
    out = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            name = Path(info.filename).name
            if info.is_dir() or not name.lower().endswith(".csv"):
                continue
            target = raw_dir / name
            with archive.open(info) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            out.append(target)
    return out


def find_nmc(raw_dir: Path) -> Path | None:
    """The raw NMC file: an official CSV if present, otherwise the mirror."""
    candidates = sorted(raw_dir.glob("NMC*.csv")) + sorted(raw_dir.glob("nmc*.csv"))
    if candidates:
        return candidates[-1]
    mirror = raw_dir / "cow_nmc.rda"
    return mirror if mirror.exists() else None


def write_extract(raw: Path, out: Path, manifest: dict) -> None:
    rows = nmc.load(raw, obtained_via=manifest.get(raw.name, {}).get("obtained_via"))
    chosen = nmc.extract(rows, EXTRACT_YEARS, EXTRACT_CCODES)
    versions = sorted({r["version"] for r in chosen})
    first, last = min(r["year"] for r in rows), max(r["year"] for r in rows)
    header = (
        f"Source: {nmc.SOURCE}, version {', '.join(versions)} ({first} to {last}).\n"
        "Extract: GMY, FRN, UKG, RUS, JPN, ITA, USA, POL; years 1933 to 1941 (Poland has no "
        "rows after 1939: it is not a member of the state system 1940 to 1944).\n"
        "Units: milex thousands of current US dollars; milper thousands; irst thousands of "
        "tons; pec thousands of coal-ton equivalents; tpop, upop thousands. -9 = missing.\n"
        f"Derived by scripts/fetch_ww2_data.py from {raw.name} (sha256 {sha256(raw)}); "
        "see data/ww2/README.md."
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    nmc.write_csv(chosen, out, header)
    print(f"extract: {shown(out)} ({len(chosen)} rows, NMC version {versions})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--mirror", action="store_true", help="fetch the peacesciencer mirrors")
    mode.add_argument("--official", action="store_true", help="fetch official COW files")
    parser.add_argument("--nmc-url", help="official NMC download URL (CSV or zip)")
    parser.add_argument("--mid-url", help="official dispute-level MID download URL")
    parser.add_argument(
        "--from-file",
        action="append",
        default=[],
        metavar="DATASET=PATH",
        help="register a local file (dataset nmc or mid)",
    )
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--extract-out", type=Path, default=EXTRACT)
    parser.add_argument("--no-extract", action="store_true")
    args = parser.parse_args(argv)

    raw_dir: Path = args.raw_dir.resolve()
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = raw_dir / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    if args.mirror:
        for dataset, url in MIRRORS.items():
            path = download(url, raw_dir / url.rsplit("/", 1)[-1])
            record(manifest, dataset, path, url, f"peacesciencer R package mirror ({url})")
    if args.official:
        urls = {"nmc": args.nmc_url, "mid": args.mid_url}
        if not any(urls.values()):
            print("--official needs --nmc-url and/or --mid-url; the links are on:")
            for dataset, page in OFFICIAL_PAGES.items():
                print(f"  {dataset}: {page}")
            return 2
        for dataset, url in urls.items():
            if not url:
                continue
            path = download(url, raw_dir / url.rsplit("/", 1)[-1].split("?")[0])
            for file in unpack(path, raw_dir):
                record(manifest, dataset, file, url, f"official download ({url})")
    for spec in args.from_file:
        dataset, sep, source = spec.partition("=")
        if not sep or dataset not in MIRRORS:
            parser.error(f"--from-file takes nmc=PATH or mid=PATH, not {spec!r}")
        src = Path(source).resolve()
        target = raw_dir / src.name
        if src != target:
            shutil.copyfile(src, target)
        record(manifest, dataset, target, str(src), f"local file {src.name}")

    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    if not args.no_extract:
        raw = find_nmc(raw_dir)
        if raw is None:
            print(f"no NMC file in {raw_dir}; run with --mirror or --official first")
            return 1
        write_extract(raw, args.extract_out.resolve(), manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
