"""The registered 1914 v1 claims and their test files carry the same text.

docs/july1914_testbed.md section 8.3 is the registration of record (J1v1 to J9v1, 2026-10-24);
each ``test_J<nn>v1.py`` carries one claim as a ``CLAIM`` dict, verbatim. These checks keep the
two from drifting apart (the pattern of tests/agi/test_registration.py). The claim literal is
read with ``ast``, not by importing the file, so that an un-skipped file with model imports is
not executed here.
"""

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "july1914_testbed.md"
HERE = Path(__file__).resolve().parent
FIELDS = ("id", "from_state", "claim", "expected", "sources")
ROW = re.compile(r"\| (J\dv1) \|")


def file_of(cid: str) -> Path:
    m = re.fullmatch(r"J(\d)v1", cid)
    assert m, cid
    return HERE / f"test_J{int(m.group(1)):02d}v1.py"


def registered_rows() -> dict[str, dict[str, str]]:
    text = DOC.read_text(encoding="utf-8")
    section = text.split("### 8.3 Registered claims (v1)", 1)[1].split("\n### ", 1)[0]
    rows = {}
    for line in section.splitlines():
        if not ROW.match(line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        assert len(cells) == len(FIELDS), f"malformed row: {line}"
        rows[cells[0]] = dict(zip(FIELDS, cells, strict=True))
    return rows


def claim_of(cid: str) -> dict[str, str]:
    tree = ast.parse(file_of(cid).read_text(encoding="utf-8"))
    node = next(
        n
        for n in tree.body
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", None) == "CLAIM"
    )
    return ast.literal_eval(node.value)


def norm(s: str) -> str:
    return " ".join(s.split())


IDS = sorted(registered_rows())


def test_the_table_registers_j1v1_to_j9v1_in_order():
    assert IDS == [f"J{i}v1" for i in range(1, 10)]


def test_every_registered_claim_has_a_file_and_no_other():
    files = sorted(p.stem for p in HERE.glob("test_J*.py"))
    assert files == sorted(file_of(cid).stem for cid in IDS)


@pytest.mark.parametrize("cid", IDS)
def test_claim_text_is_verbatim(cid):
    row = registered_rows()[cid]
    claim = claim_of(cid)
    assert set(claim) == set(FIELDS)
    for key in FIELDS:
        assert norm(claim[key]) == norm(row[key]), f"{cid}.{key} differs from the document"
