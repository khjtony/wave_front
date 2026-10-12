"""The NMC and MID loaders, the committed NMC extract and the fetch script (offline parts)."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from wavefront.evidence.datasets import mid, nmc

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
EXTRACT = ROOT / "data" / "ww2" / "nmc_1936_1940.csv"
RAW = ROOT / "data" / "ww2" / "raw"
WW2_CCODES = {2, 200, 220, 255, 290, 325, 365, 740}


def fetch_script():
    spec = importlib.util.spec_from_file_location(
        "fetch_ww2_data", ROOT / "scripts" / "fetch_ww2_data.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# -- NMC ------------------------------------------------------------------------------------


def test_nmc_official_csv_rows_and_provenance():
    rows = nmc.load(FIXTURES / "nmc_sample.csv")
    assert len(rows) == 20
    assert list(rows[0]) == [*nmc.COLUMNS, "source", "obtained_via"]
    for row in rows:
        assert row["source"] == nmc.SOURCE
        assert row["version"] == "7.0"
        assert row["obtained_via"] == "local file nmc_sample.csv"
        assert isinstance(row["ccode"], int) and isinstance(row["year"], int)
    gmy_1938 = next(r for r in rows if r["ccode"] == 255 and r["year"] == 1938)
    assert gmy_1938["stateabb"] == "GMY"
    assert (gmy_1938["milex"], gmy_1938["milper"], gmy_1938["irst"]) == (7415163, 782, 22656)
    assert isinstance(gmy_1938["cinc"], float)


def test_nmc_missing_code_becomes_none():
    rows = nmc.load(FIXTURES / "nmc_sample.csv")
    italy_1941 = next(r for r in rows if r["ccode"] == 325 and r["year"] == 1941)
    assert italy_1941["milper"] is None
    assert italy_1941["milex"] == 541238


def test_nmc_extract_filters_and_orders():
    rows = nmc.load(FIXTURES / "nmc_sample.csv")
    chosen = nmc.extract(rows, years=[1937, 1938], ccodes=[365, 255])
    assert [(r["ccode"], r["year"]) for r in chosen] == [
        (255, 1937),
        (255, 1938),
        (365, 1937),
        (365, 1938),
    ]
    assert nmc.value(rows, 365, 1938, "milper") == 1566
    with pytest.raises(KeyError):
        nmc.value(rows, 365, 1950, "milper")


def test_nmc_write_csv_round_trip(tmp_path):
    rows = nmc.load(FIXTURES / "nmc_sample.csv", obtained_via="a test copy")
    out = tmp_path / "extract.csv"
    nmc.write_csv(rows, out, "Source: NMC version 7.0\nsecond line")
    text = out.read_text(encoding="utf-8").splitlines()
    assert text[:3] == ["# Source: NMC version 7.0", "# second line", "# obtained_via: a test copy"]
    assert text[3] == ",".join(nmc.COLUMNS)
    assert any(",-9," in line for line in text)  # the missing Italian milper
    assert nmc.load(out) == rows


def test_nmc_version_inferred_from_coverage(tmp_path):
    for last, version in ((2016, "6.0"), (2022, "7.0"), (1999, "unknown (coverage ends 1999)")):
        path = tmp_path / f"nmc_{last}.csv"
        path.write_text(f"ccode,year,milex\n255,1938,7415163\n2,{last},1\n", encoding="utf-8")
        rows = nmc.load(path)
        assert {r["version"] for r in rows} == {version}
        assert rows[0]["stateabb"] == "GMY" and rows[0]["irst"] is None
    assert {r["version"] for r in nmc.load(path, version="5.0")} == {"5.0"}


def test_nmc_rejects_other_tables(tmp_path):
    path = tmp_path / "other.csv"
    path.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="not an NMC table"):
        nmc.load(path)


def test_nmc_rda_fixture(tmp_path):
    pytest.importorskip("pyreadr")
    rows = nmc.load(FIXTURES / "nmc_sample.rda")
    assert len(rows) == 8
    assert {r["stateabb"] for r in rows} == {"GMY", "ITA"}
    assert rows[0]["version"] == "unknown (coverage ends 1941)"
    assert rows[0]["obtained_via"] == "local file nmc_sample.rda"
    italy_1941 = next(r for r in rows if r["ccode"] == 325 and r["year"] == 1941)
    assert italy_1941["milper"] is None  # NaN in R
    csv_rows = {(r["ccode"], r["year"]): r for r in nmc.load(FIXTURES / "nmc_sample.csv")}
    for row in rows:
        for column in ("milex", "milper", "irst", "pec", "tpop", "upop"):
            assert row[column] == csv_rows[(row["ccode"], row["year"])][column]
    # The mirror's file name selects the mirror as the default provenance.
    mirror = tmp_path / "cow_nmc.rda"
    mirror.write_bytes((FIXTURES / "nmc_sample.rda").read_bytes())
    assert nmc.load(mirror, version="7.0")[0]["obtained_via"] == nmc.MIRROR_NOTE


def test_core_does_not_import_pyreadr():
    code = (
        "import sys\n"
        "import wavefront.evidence, wavefront.evidence.datasets, wavefront.evidence.hindsight_ww2\n"
        "from wavefront.evidence.datasets import nmc\n"
        f"nmc.load({str(FIXTURES / 'nmc_sample.csv')!r})\n"
        "assert 'pyreadr' not in sys.modules and 'pandas' not in sys.modules\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True, cwd=ROOT)


# -- the committed extract ------------------------------------------------------------------


def test_committed_extract_shape_and_header():
    header = [
        line for line in EXTRACT.read_text(encoding="utf-8").splitlines() if line.startswith("#")
    ]
    assert "National Material Capabilities" in header[0] and "version 7.0" in header[0]
    assert any("Singer, Bremer and Stuckey 1972; Singer 1988" in line for line in header)
    assert any(line.startswith("# obtained_via: peacesciencer") for line in header)
    rows = nmc.load(EXTRACT)
    assert {r["ccode"] for r in rows} == WW2_CCODES
    assert {r["year"] for r in rows} == set(range(1933, 1942))
    # Poland leaves the state system after 1939; every other state has nine years.
    assert len(rows) == 7 * 9 + 7
    assert max(r["year"] for r in rows if r["ccode"] == 290) == 1939
    assert {r["version"] for r in rows} == {"7.0"}


@pytest.mark.parametrize(
    ("ccode", "year", "milex", "milper", "irst"),
    [
        (255, 1936, 2332782, 596, 19208),
        (255, 1939, 12000000, 2750, 23733),
        (200, 1939, 7895671, 394, 13433),
        (220, 1940, 5707762, 5000, 4413),
        (365, 1937, 3446172, 1433, 17730),
    ],
)
def test_committed_extract_values(ccode, year, milex, milper, irst):
    rows = nmc.load(EXTRACT)
    assert [nmc.value(rows, ccode, year, c) for c in ("milex", "milper", "irst")] == [
        milex,
        milper,
        irst,
    ]


def test_raw_mirror_reproduces_the_extract():
    raw = RAW / "cow_nmc.rda"
    if not raw.exists():
        pytest.skip("data/ww2/raw/cow_nmc.rda not fetched (scripts/fetch_ww2_data.py --mirror)")
    pytest.importorskip("pyreadr")
    rows = nmc.load(raw)
    assert {r["version"] for r in rows} == {"7.0"}
    fresh = nmc.extract(rows, range(1933, 1942), WW2_CCODES)
    assert fresh == nmc.load(EXTRACT)


# -- MID ------------------------------------------------------------------------------------


def test_mid_csv():
    rows = mid.load(FIXTURES / "mid_sample.csv")
    assert len(rows) == 5
    first = rows[0]
    assert first["dispnum"] == 9001 and first["styear"] == 1936
    assert first["endday"] is None  # -9
    assert first["version"] == "5.0"
    assert first["source"] == mid.SOURCE
    assert first["obtained_via"] == "local file mid_sample.csv"
    assert [r["dispnum"] for r in mid.in_years(rows, 1936, 1940)] == [9001, 9002, 9003, 9004]


def test_mid_rejects_other_tables(tmp_path):
    path = tmp_path / "x.csv"
    path.write_text("a\n1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="dispnum"):
        mid.load(path)


def test_mid_rda_fixture(tmp_path):
    pytest.importorskip("pyreadr")
    rows = mid.load(FIXTURES / "mid_sample.rda")
    assert len(rows) == 6
    assert all(isinstance(r["dispnum"], int) for r in rows)
    assert any(r["fatality"] is None for r in rows)  # -9 in the source
    assert rows[0]["version"] == "unknown"
    mirror = tmp_path / "cow_mid_disps.rda"
    mirror.write_bytes((FIXTURES / "mid_sample.rda").read_bytes())
    row = mid.load(mirror)[0]
    assert (row["version"], row["obtained_via"]) == ("5.0", mid.MIRROR_NOTE)


def test_raw_mid_mirror():
    raw = RAW / "cow_mid_disps.rda"
    if not raw.exists():
        pytest.skip("data/ww2/raw/cow_mid_disps.rda not fetched")
    pytest.importorskip("pyreadr")
    rows = mid.load(raw)
    assert {r["version"] for r in rows} == {"5.0"}
    assert mid.in_years(rows, 1936, 1940)


# -- the fetch script, offline ----------------------------------------------------------------


def test_fetch_script_writes_extract_from_a_local_file(tmp_path):
    script = fetch_script()
    raw_dir = tmp_path / "raw"
    out = tmp_path / "extract.csv"
    status = script.main(
        [
            "--raw-dir",
            str(raw_dir),
            "--extract-out",
            str(out),
            "--from-file",
            f"nmc={FIXTURES / 'nmc_sample.csv'}",
        ]
    )
    assert status == 0
    manifest = (raw_dir / "MANIFEST.json").read_text(encoding="utf-8")
    assert "nmc_sample.csv" in manifest and "sha256" in manifest
    text = out.read_text(encoding="utf-8")
    assert "version 7.0" in text and script.sha256(raw_dir / "nmc_sample.csv") in text
    rows = nmc.load(out)
    assert {r["ccode"] for r in rows} == {200, 220, 255, 325, 365}
    assert rows[0]["obtained_via"] == "local file nmc_sample.csv"


def test_fetch_script_official_needs_a_url(tmp_path, capsys):
    script = fetch_script()
    status = script.main(["--official", "--raw-dir", str(tmp_path), "--no-extract"])
    assert status == 2
    assert "correlatesofwar.org" in capsys.readouterr().out
