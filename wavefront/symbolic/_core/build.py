"""Build the compiled BDD core: ``python -m wavefront.symbolic._core.build``.

cffi in out-of-line API mode compiles ``bdd_core.c`` with the declarations of the
``cffi-begin`` to ``cffi-end`` region of ``bdd_core.h`` into the extension module
``wavefront/symbolic/_core/_bdd*.so``, next to this file, which is where an editable install
imports it from. Needs the ``fast`` extra (cffi) and a C11 compiler. ``--debug`` builds
without optimization and with debug symbols; ``--cc`` picks the compiler (default: the one
Python was built with, or ``$CC``).
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

from cffi import FFI

from . import HERE, source_hash

MODULE = "wavefront.symbolic._core._bdd"


def declarations() -> str:
    """The declarations cffi exposes: the marked region of ``bdd_core.h``, with each
    ``#define``'s value replaced by ``...`` (cffi reads it from the compiled header)."""
    text = (HERE / "bdd_core.h").read_text()
    region = text.split("cffi-begin", 1)[1].split("*/", 1)[1].split("/* cffi-end */", 1)[0]
    region = re.sub(r"/\*.*?\*/", "", region, flags=re.S)
    return re.sub(r"^#define (\w+) .*$", r"#define \1 ...", region, flags=re.M)


def builder(debug: bool = False) -> FFI:
    """The cffi builder of the extension module."""
    ffi = FFI()
    ffi.cdef(declarations())
    flags = ["-std=c11", "-O0", "-g"] if debug else ["-std=c11", "-O3", "-g", "-DNDEBUG"]
    ffi.set_source(
        MODULE,
        '#include "bdd_core.h"',
        sources=[str(HERE / "bdd_core.c")],
        include_dirs=[str(HERE)],
        define_macros=[("BDD_SOURCE_HASH", f'"{source_hash()}"')],
        extra_compile_args=flags,
    )
    return ffi


def build(debug: bool = False, verbose: bool = False) -> Path:
    """Compile the module in a temporary directory and copy it next to the sources."""
    ffi = builder(debug)
    with tempfile.TemporaryDirectory(prefix="wavefront-bdd-") as tmp:
        built = Path(ffi.compile(tmpdir=tmp, verbose=verbose))
        for old in HERE.glob("_bdd*.so"):
            old.unlink()
        for old in HERE.glob("_bdd*.pyd"):
            old.unlink()
        target = HERE / built.name
        shutil.copy2(built, target)
    return target


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--debug", action="store_true", help="no optimization, debug symbols")
    p.add_argument("--cc", default=None, help="C compiler (sets $CC)")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)
    if args.cc:
        os.environ["CC"] = args.cc
    target = build(args.debug, args.verbose)
    print(f"built {target} (sources {source_hash()})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
