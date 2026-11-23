"""Build the Sylvan core: ``python -m wavefront.symbolic._sylvan.build``.

Two steps. First Sylvan itself (and Lace, which its build fetches): the pinned commit is
cloned into ``third_party/sylvan`` at the repository root, built with cmake as static
position-independent libraries and installed into ``third_party/install``. Then cffi compiles
``wf_sylvan.c`` against that prefix into ``wavefront/symbolic/_sylvan/_sylvan*.so``.

``--prefix DIR`` (or ``$WAVEFRONT_SYLVAN_PREFIX``) names an existing installation of Sylvan
and Lace (``include/sylvan.h``, ``lib/libsylvan.a``, ``lib/liblace.a``, built with
``-fPIC``) and skips the first step. Needs the ``fast`` extra (cffi), a C11 compiler, and
for the first step git and cmake 3.23 or later (``pip install cmake`` provides one).
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from cffi import FFI

from . import HERE, source_hash

MODULE = "wavefront.symbolic._sylvan._sylvan"
ROOT = HERE.parents[2]
THIRD_PARTY = ROOT / "third_party"
SYLVAN_URL = "https://github.com/trolando/sylvan.git"
SYLVAN_COMMIT = "cd934c18bc5a7b1caabc87915deeeaf588afba41"  # 1.12.8, with Lace 1.11.1


def _tool(name: str) -> str:
    """``name`` on the path or next to the interpreter (a pip-installed cmake)."""
    found = shutil.which(name) or shutil.which(name, path=str(Path(sys.executable).parent))
    if found is None:
        raise SystemExit(f"{name} not found (needed to build Sylvan)")
    return found


def build_sylvan(jobs: int = 4, verbose: bool = False) -> Path:
    """Clone, build and install Sylvan under ``third_party``; return the prefix."""
    src, out, prefix = THIRD_PARTY / "sylvan", THIRD_PARTY / "sylvan-build", THIRD_PARTY / "install"
    quiet = None if verbose else subprocess.DEVNULL
    git, cmake = _tool("git"), _tool("cmake")
    if not (src / "CMakeLists.txt").exists():
        src.mkdir(parents=True, exist_ok=True)
        for cmd in (
            ["init", "-q"],
            ["fetch", "-q", "--depth", "1", SYLVAN_URL, SYLVAN_COMMIT],
            ["checkout", "-q", "FETCH_HEAD"],
        ):
            subprocess.run([git, "-C", str(src), *cmd], check=True)
    subprocess.run(
        [
            cmake,
            "-S",
            str(src),
            "-B",
            str(out),
            "-DCMAKE_BUILD_TYPE=Release",
            "-DSYLVAN_ENABLE_PIC=ON",
            "-DSYLVAN_BUILD_CPP=OFF",
            "-DSYLVAN_BUILD_TESTS=OFF",
            "-DSYLVAN_BUILD_EXAMPLES=OFF",
            "-DSYLVAN_BUILD_DOCS=OFF",
            "-DSYLVAN_INSTALL=ON",
            f"-DCMAKE_INSTALL_PREFIX={prefix}",
        ],
        check=True,
        stdout=quiet,
    )
    subprocess.run([cmake, "--build", str(out), "-j", str(jobs)], check=True, stdout=quiet)
    subprocess.run([cmake, "--install", str(out)], check=True, stdout=quiet)
    return prefix


def declarations() -> str:
    """The declarations cffi exposes: the marked region of ``wf_sylvan.h``."""
    text = (HERE / "wf_sylvan.h").read_text()
    region = text.split("cffi-begin", 1)[1].split("*/", 1)[1].split("/* cffi-end */", 1)[0]
    region = re.sub(r"/\*.*?\*/", "", region, flags=re.S)
    return re.sub(r"^#define (\w+) .*$", r"#define \1 ...", region, flags=re.M)


def builder(prefix: Path, debug: bool = False) -> FFI:
    """The cffi builder of the extension module."""
    ffi = FFI()
    ffi.cdef(declarations())
    flags = ["-std=c11", "-O0", "-g"] if debug else ["-std=c11", "-O3", "-g", "-DNDEBUG"]
    ffi.set_source(
        MODULE,
        '#include "wf_sylvan.h"',
        sources=[str(HERE / "wf_sylvan.c")],
        include_dirs=[str(HERE), str(prefix / "include")],
        define_macros=[("WFS_SOURCE_HASH", f'"{source_hash()}"')],
        extra_compile_args=flags,
        extra_objects=[str(prefix / "lib" / "libsylvan.a"), str(prefix / "lib" / "liblace.a")],
        libraries=["pthread", "m"],
    )
    return ffi


def build(prefix: Path, debug: bool = False, verbose: bool = False) -> Path:
    """Compile the module in a temporary directory and copy it next to the sources."""
    ffi = builder(prefix, debug)
    with tempfile.TemporaryDirectory(prefix="wavefront-sylvan-") as tmp:
        built = Path(ffi.compile(tmpdir=tmp, verbose=verbose))
        for old in HERE.glob("_sylvan*.so"):
            old.unlink()
        target = HERE / built.name
        shutil.copy2(built, target)
    return target


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--prefix", default=os.environ.get("WAVEFRONT_SYLVAN_PREFIX"))
    p.add_argument("--debug", action="store_true", help="no optimization, debug symbols")
    p.add_argument("--cc", default=None, help="C compiler (sets $CC)")
    p.add_argument("-j", "--jobs", type=int, default=4, help="parallel jobs of the Sylvan build")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)
    if args.cc:
        os.environ["CC"] = args.cc
    prefix = Path(args.prefix).resolve() if args.prefix else build_sylvan(args.jobs, args.verbose)
    target = build(prefix, args.debug, args.verbose)
    print(f"built {target} (sources {source_hash()}, Sylvan from {prefix})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
