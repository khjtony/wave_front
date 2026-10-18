"""The registered AGI claims and their test files carry the same text.

docs/agi_testbed.md section 5 is the registration of record (G1 to G22, 2026-10-17); each
``tests/agi/scenarios/test_G<nn>.py`` carries one claim as a ``CLAIM`` dict, verbatim. These
checks keep the two from drifting apart: an edit to either side without the other shows up
here, and the protocol (agi_testbed.md section 6) requires a changelog line for any edit. An
amended claim is a new row ``G<n>a`` with its own file ``test_G<nn>a.py`` (section 6, item 2).

The claim literal is read with ``ast``, not by importing the file, so that an un-skipped test
file with model imports (the shape of tests/july1914/test_J01.py) is not executed here.
"""

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "agi_testbed.md"
SCENARIOS = ROOT / "tests" / "agi" / "scenarios"
FIRST_SIGHT = ROOT / "tests" / "agi" / "test_model_agi.py"
FIELDS = ("id", "from_state", "claim", "expected", "sources")
ROW = re.compile(r"\| (G\d+a?) \|")  # one amendment per claim: the suffix is "a" only


def file_of(cid: str) -> Path:
    m = re.fullmatch(r"G(\d+)(a?)", cid)
    assert m, cid
    return SCENARIOS / f"test_G{int(m.group(1)):02d}{m.group(2)}.py"


def registered_rows() -> dict[str, dict[str, str]]:
    """The rows of the claim table in section 5, keyed by id, with ``\\|`` unescaped."""
    text = DOC.read_text(encoding="utf-8")
    section = text.split("## 5. Registered claims", 1)[1].split("\n## ", 1)[0]
    rows = {}
    for line in section.splitlines():
        if not ROW.match(line):
            continue
        cells = [
            c.replace("\\|", "|").strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))
        ]
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


IDS = sorted(registered_rows(), key=lambda x: (int(re.match(r"G(\d+)", x).group(1)), x))


def test_the_table_registers_g1_to_g22_in_order():
    base = [i for i in IDS if i[-1].isdigit()]
    assert base == [f"G{i}" for i in range(1, 23)]


def test_every_registered_claim_has_a_file_and_no_other():
    files = sorted(p.stem for p in SCENARIOS.glob("test_G*.py"))
    assert all(re.fullmatch(r"test_G\d{2}a?", f) for f in files), files
    assert files == sorted(file_of(cid).stem for cid in IDS)


@pytest.mark.parametrize("cid", IDS)
def test_claim_text_is_verbatim(cid):
    row = registered_rows()[cid]
    claim = claim_of(cid)
    assert set(claim) == set(FIELDS)
    for key in FIELDS:
        assert norm(claim[key]) == norm(row[key]), f"{cid}.{key} differs from the document"


@pytest.mark.parametrize("cid", IDS)
def test_stub_is_skipped_until_first_sight_is_recorded(cid):
    """A registered claim stays a skipped stub until the model step un-skips it, and an
    un-skipped file is allowed only once ``tests/agi/test_model_agi.py`` records the commit of
    first sight as a 40-hex ``FIRST_SIGHT_COMMIT`` (agi_testbed.md section 6, item 1)."""
    tree = ast.parse(file_of(cid).read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == f"test_{cid}")
    skipped = any(
        isinstance(d, ast.Call) and ast.unparse(d.func) == "pytest.mark.skip"
        for d in fn.decorator_list
    )
    if skipped:
        return
    assert FIRST_SIGHT.exists(), f"{cid} is un-skipped but no first-sight record exists"
    assert re.search(
        r'^FIRST_SIGHT_COMMIT = "[0-9a-f]{40}"$', FIRST_SIGHT.read_text(encoding="utf-8"), re.M
    ), "tests/agi/test_model_agi.py must record FIRST_SIGHT_COMMIT as a 40-hex commit"
