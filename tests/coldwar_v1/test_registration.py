"""The registered cw_v1 claims and their test files carry the same text.

docs/coldwar_testbed.md section 9 is the registration of record (V1 to V10, 2026-10-24); each
``tests/coldwar_v1/scenarios/test_V<nn>.py`` carries one claim as a ``CLAIM`` dict, verbatim.
An edit to either side without the other shows up here, and the protocol requires a changelog
line for any edit (section 8). An amended claim is a new row ``V<n>a`` with its own file
``test_V<nn>a.py``.

The claim literal is read with ``ast``, not by importing the file, so that an un-skipped test
file with model imports is not executed here.
"""

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "coldwar_testbed.md"
SCENARIOS = ROOT / "tests" / "coldwar_v1" / "scenarios"
FIELDS = ("id", "from_state", "claim", "expected", "sources")
ROW = re.compile(r"\| (V\d+a?) \|")


def file_of(cid: str) -> Path:
    m = re.fullmatch(r"V(\d+)(a?)", cid)
    assert m, cid
    return SCENARIOS / f"test_V{int(m.group(1)):02d}{m.group(2)}.py"


def registered_rows() -> dict[str, dict[str, str]]:
    """The rows of the claim table in section 9.3, keyed by id."""
    text = DOC.read_text(encoding="utf-8")
    section = text.split("## 9. cw_v1 registration", 1)[1].split("\n### 9.4", 1)[0]
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


IDS = sorted(registered_rows(), key=lambda x: (int(re.match(r"V(\d+)", x).group(1)), x))


def test_the_table_registers_v1_to_v10_in_order():
    assert [i for i in IDS if i[-1].isdigit()] == [f"V{i}" for i in range(1, 11)]


def test_every_registered_claim_has_a_file_and_no_other():
    files = sorted(p.stem for p in SCENARIOS.glob("test_V*.py"))
    assert all(re.fullmatch(r"test_V\d{2}a?", f) for f in files), files
    assert files == sorted(file_of(cid).stem for cid in IDS)


@pytest.mark.parametrize("cid", IDS)
def test_claim_text_is_verbatim(cid):
    row = registered_rows()[cid]
    claim = claim_of(cid)
    assert set(claim) == set(FIELDS)
    for key in FIELDS:
        assert norm(claim[key]) == norm(row[key]), f"{cid}.{key} differs from the document"


@pytest.mark.parametrize("cid", IDS)
def test_stub_skips_until_cw_v1_is_built(cid):
    """Each stub is guarded by ``skipif(not BUILT, reason="cw_v1 not built")`` until the model
    step replaces it with its reading."""
    src = file_of(cid).read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == f"test_{cid}")
    if not any(isinstance(n, ast.Raise) for n in ast.walk(fn)):
        return  # the model step has written the reading
    decos = [ast.unparse(d) for d in fn.decorator_list]
    assert "pytest.mark.skipif(not BUILT, reason='cw_v1 not built')" in decos, decos
