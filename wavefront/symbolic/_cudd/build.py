"""Build the CUDD binding: ``python -m wavefront.symbolic._cudd.build``.

cffi in out-of-line API mode compiles ``wf_cudd.c`` with the declarations of the
``cffi-begin`` to ``cffi-end`` region of ``wf_cudd.h`` and links CUDD's static library into
the extension module ``wavefront/symbolic/_cudd/_cudd*.so``.

CUDD itself is not part of the repository. ``--cudd DIR`` (or ``$WAVEFRONT_CUDD_SRC``) names
a CUDD 3.0.0 source tree in which ``./configure CFLAGS="-O3 -fPIC" && make`` has run; the
default is ``third_party/cudd-cudd-3.0.0`` at the repository root. ``--fetch`` downloads the
3.0.0 sources there and compiles them first (needs network access, ``tar`` and ``make``).
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from cffi import FFI

from . import HERE, source_hash

MODULE = "wavefront.symbolic._cudd._cudd"
ROOT = HERE.parents[2]
THIRD_PARTY = ROOT / "third_party"
DEFAULT_SRC = THIRD_PARTY / "cudd-cudd-3.0.0"
URL = "https://github.com/ivmai/cudd/archive/refs/tags/cudd-3.0.0.tar.gz"


def cudd_src(path: str | None = None) -> Path:
    """The CUDD source tree to build against."""
    return Path(path or os.environ.get("WAVEFRONT_CUDD_SRC") or DEFAULT_SRC).resolve()


def fetch(src: Path = DEFAULT_SRC) -> Path:
    """Download CUDD 3.0.0 and compile its static library with ``-fPIC``."""
    src.parent.mkdir(parents=True, exist_ok=True)
    if not (src / "configure").exists():
        with tempfile.TemporaryDirectory(prefix="wavefront-cudd-") as tmp:
            archive = Path(tmp) / "cudd.tar.gz"
            urllib.request.urlretrieve(URL, archive)  # noqa: S310 (a fixed https URL)
            subprocess.run(["tar", "xzf", str(archive), "-C", str(src.parent)], check=True)
    if not (src / "cudd" / ".libs" / "libcudd.a").exists():
        subprocess.run(["./configure", "CFLAGS=-O3 -fPIC -g"], cwd=src, check=True)
        subprocess.run(["make", "-j4"], cwd=src, check=True)
    return src


def declarations() -> str:
    """The declarations cffi exposes: the marked region of ``wf_cudd.h``."""
    text = (HERE / "wf_cudd.h").read_text()
    region = text.split("cffi-begin", 1)[1].split("*/", 1)[1].split("/* cffi-end */", 1)[0]
    region = re.sub(r"/\*.*?\*/", "", region, flags=re.S)
    region = re.sub(r"^#define (\w+) .*$", r"#define \1 ...", region, flags=re.M)
    return "typedef struct DdManager DdManager;\n" + region


def builder(src: Path, debug: bool = False) -> FFI:
    """The cffi builder of the extension module."""
    lib = src / "cudd" / ".libs" / "libcudd.a"
    if not lib.exists():
        raise FileNotFoundError(
            f"{lib} not found: compile CUDD there first, or run this module with --fetch"
        )
    ffi = FFI()
    ffi.cdef(declarations())
    flags = ["-std=c11", "-O0", "-g"] if debug else ["-std=c11", "-O3", "-g", "-DNDEBUG"]
    ffi.set_source(
        MODULE,
        '#include "wf_cudd.h"',
        sources=[str(HERE / "wf_cudd.c")],
        include_dirs=[str(HERE), str(src), str(src / "cudd"), str(src / "mtr")],
        define_macros=[("WF_SOURCE_HASH", f'"{source_hash()}"')],
        extra_compile_args=flags,
        extra_objects=[str(lib)],
        libraries=["m"],
    )
    return ffi


def build(src: Path, debug: bool = False, verbose: bool = False) -> Path:
    """Compile the module in a temporary directory and copy it next to the sources."""
    ffi = builder(src, debug)
    with tempfile.TemporaryDirectory(prefix="wavefront-cudd-") as tmp:
        built = Path(ffi.compile(tmpdir=tmp, verbose=verbose))
        for old in HERE.glob("_cudd*.so"):
            old.unlink()
        target = HERE / built.name
        shutil.copy2(built, target)
    return target


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--cudd", default=None, help="compiled CUDD 3.0.0 source tree")
    p.add_argument("--fetch", action="store_true", help="download and compile CUDD first")
    p.add_argument("--debug", action="store_true", help="no optimization, debug symbols")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)
    src = cudd_src(args.cudd)
    if args.fetch:
        fetch(src)
    target = build(src, args.debug, args.verbose)
    print(f"built {target} (shim sources {source_hash()}, CUDD at {src})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
