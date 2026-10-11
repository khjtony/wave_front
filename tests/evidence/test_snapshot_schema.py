"""The snapshot schema and the hand-written validator that implements it."""

import copy
import json
import re
from pathlib import Path

import pytest

from wavefront.evidence import validate_snapshot

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "snapshots" / "schema.json"
EXAMPLE_PATH = ROOT / "snapshots" / "toy" / "example.json"
DESIGN_PATH = ROOT / "docs" / "DESIGN.md"

# The example of DESIGN.md section 5.1, verbatim.
DESIGN_EXAMPLE = {
    "date": "2026-10-11",
    "model": "v0_toy",
    "variables": {
        "oversight": {
            "level": "weak",
            "confidence": "medium",
            "indicators": [
                {
                    "id": "frontier_safety_frameworks",
                    "value": "...",
                    "source": "<url>",
                    "observed": "2026-09-30",
                    "rule": "voluntary frameworks without external audit -> weak",
                }
            ],
        }
    },
    "rates": {"lag_regime": {"ticks": 7, "basis": "EU AI Act adoption-to-obligation timeline"}},
}


def schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def example():
    return json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))


def indicator():
    return {
        "id": "i",
        "value": "v",
        "source": "https://example.org/s",
        "observed": "2026-09-30",
        "rule": "r",
    }


def doc(**variable):
    """A small valid snapshot with one variable ``v``; keyword arguments override its fields."""
    entry = {"level": "weak", "confidence": "high", "indicators": [indicator()]}
    entry.update(variable)
    return {"date": "2026-10-11", "model": "m", "variables": {"v": entry}}


# -- the schema file ---------------------------------------------------------------------


def test_the_schema_is_a_draft_2020_12_schema_with_the_required_shape():
    s = schema()
    assert s["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert s["type"] == "object" and s["additionalProperties"] is False
    assert s["required"] == ["date", "model", "variables"]
    assert set(s["properties"]) == {"$schema", "date", "model", "variables", "rates"}
    defs = s["$defs"]
    assert defs["variable"]["required"] == ["level", "confidence", "indicators"]
    assert defs["variable"]["properties"]["confidence"]["enum"] == [
        "high",
        "medium",
        "low",
        "assumed",
    ]
    assert defs["indicator"]["required"] == ["id", "value", "source", "observed", "rule"]
    assert defs["rate"]["required"] == ["ticks", "basis"]


def test_the_schema_is_itself_valid():
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.Draft202012Validator.check_schema(schema())


# -- documents that must validate ----------------------------------------------------------


def test_the_design_example_validates():
    assert validate_snapshot(DESIGN_EXAMPLE) == []


def test_the_example_in_design_md_still_validates():
    """DESIGN.md is the format's source of truth: if its example drifts from the schema this
    fails, whichever of the two was edited."""
    text = DESIGN_PATH.read_text(encoding="utf-8")
    section = text.split("### 5.1", 1)[1]
    block = re.search(r"```json\n(.*?)\n```", section, re.DOTALL)
    assert block, "DESIGN.md section 5.1 no longer has a json example"
    assert validate_snapshot(json.loads(block.group(1))) == []


def test_the_toy_example_validates_and_has_provenance_on_every_variable():
    data = example()
    assert validate_snapshot(data) == []
    assert data["variables"]
    for name, entry in data["variables"].items():
        assert entry["indicators"], name
        assert all("example" in i["source"].lower() for i in entry["indicators"]), name


def test_an_assumed_variable_may_have_no_indicators_and_rates_are_optional():
    data = doc(confidence="assumed", indicators=[])
    assert validate_snapshot(data) == []
    assert "rates" not in data
    data["variables"] = {}
    assert validate_snapshot(data) == []


def test_every_kind_of_level_is_structurally_valid():
    for level in ("weak", 3, 3.0, True, False, 0):
        assert validate_snapshot(doc(level=level)) == [], level


def test_indicator_values_may_be_strings_numbers_or_booleans():
    for value in ("text", 0, 12.5, True, False):
        data = doc()
        data["variables"]["v"]["indicators"][0]["value"] = value
        assert validate_snapshot(data) == [], value


# -- documents that must be refused ----------------------------------------------------------


def broken(mutate):
    data = doc()
    mutate(data)
    return data


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ([], r"snapshot: must be an object"),
        ("snapshot", r"snapshot: must be an object"),
        (broken(lambda d: d.pop("date")), r"snapshot: missing required field 'date'"),
        (broken(lambda d: d.pop("model")), r"snapshot: missing required field 'model'"),
        (broken(lambda d: d.pop("variables")), r"snapshot: missing required field 'variables'"),
        (broken(lambda d: d.update(extra=1)), r"snapshot: unexpected field 'extra'"),
        (broken(lambda d: d.update(date="11-10-2026")), r"date: '11-10-2026' is not a date"),
        (broken(lambda d: d.update(date="2026-1-5")), r"date: '2026-1-5' is not a date in YYYY"),
        (broken(lambda d: d.update(date="2026-10-11T08:00")), r"date: .* is not a date"),
        (broken(lambda d: d.update(date=20261011)), r"date: 20261011 is not a date"),
        (broken(lambda d: d.update(date="2026-02-30")), r"date: '2026-02-30' is not a calendar"),
        (broken(lambda d: d.update(date="2026-13-01")), r"date: '2026-13-01' is not a calendar"),
        (broken(lambda d: d.update(model="")), r"model: must be a non-empty string"),
        (broken(lambda d: d.update(model=3)), r"model: must be a non-empty string"),
        (broken(lambda d: d.update(variables=[])), r"variables: must be an object"),
        (
            broken(lambda d: d["variables"].update({"bad name": d["variables"]["v"]})),
            r"variables: 'bad name' is not a valid variable name",
        ),
        (broken(lambda d: d["variables"].update(v=None)), r"variables\.v: must be an object"),
        (
            broken(lambda d: d["variables"]["v"].pop("level")),
            r"variables\.v: missing required field 'level'",
        ),
        (
            broken(lambda d: d["variables"]["v"].pop("confidence")),
            r"variables\.v: missing required field 'confidence'",
        ),
        (
            broken(lambda d: d["variables"]["v"].pop("indicators")),
            r"variables\.v: missing required field 'indicators'",
        ),
        (
            broken(lambda d: d["variables"]["v"].update(note="x")),
            r"variables\.v: unexpected field 'note'",
        ),
        (
            broken(lambda d: d["variables"]["v"].update(level=None)),
            r"variables\.v\.level: must be a level name, an integer or a boolean",
        ),
        (
            broken(lambda d: d["variables"]["v"].update(level=1.5)),
            r"variables\.v\.level: must be a level name",
        ),
        (
            broken(lambda d: d["variables"]["v"].update(level="")),
            r"variables\.v\.level: must not be an empty string",
        ),
        (
            broken(lambda d: d["variables"]["v"].update(confidence="certain")),
            r"variables\.v\.confidence: 'certain' is not one of high, medium, low, assumed",
        ),
        (
            broken(lambda d: d["variables"]["v"].update(indicators={})),
            r"variables\.v\.indicators: must be an array",
        ),
        (
            broken(lambda d: d["variables"]["v"]["indicators"].append("seen")),
            r"variables\.v\.indicators\[1\]: must be an object",
        ),
        (
            broken(lambda d: d["variables"]["v"]["indicators"][0].pop("source")),
            r"variables\.v\.indicators\[0\]: missing required field 'source'",
        ),
        (
            broken(lambda d: d["variables"]["v"]["indicators"][0].pop("observed")),
            r"variables\.v\.indicators\[0\]: missing required field 'observed'",
        ),
        (
            broken(lambda d: d["variables"]["v"]["indicators"][0].pop("rule")),
            r"variables\.v\.indicators\[0\]: missing required field 'rule'",
        ),
        (
            broken(lambda d: d["variables"]["v"]["indicators"][0].pop("id")),
            r"variables\.v\.indicators\[0\]: missing required field 'id'",
        ),
        (
            broken(lambda d: d["variables"]["v"]["indicators"][0].pop("value")),
            r"variables\.v\.indicators\[0\]: missing required field 'value'",
        ),
        (
            broken(lambda d: d["variables"]["v"]["indicators"][0].update(source="")),
            r"variables\.v\.indicators\[0\]\.source: must be a non-empty string",
        ),
        (
            broken(lambda d: d["variables"]["v"]["indicators"][0].update(value=None)),
            r"variables\.v\.indicators\[0\]\.value: must be a string, number or boolean",
        ),
        (
            broken(lambda d: d["variables"]["v"]["indicators"][0].update(observed="soon")),
            r"variables\.v\.indicators\[0\]\.observed: 'soon' is not a date",
        ),
        (
            broken(lambda d: d["variables"]["v"]["indicators"][0].update(colour="red")),
            r"variables\.v\.indicators\[0\]: unexpected field 'colour'",
        ),
        (
            broken(lambda d: d.update(rates=[])),
            r"rates: must be an object",
        ),
        (
            broken(lambda d: d.update(rates={"lag": {"basis": "b"}})),
            r"rates\.lag: missing required field 'ticks'",
        ),
        (
            broken(lambda d: d.update(rates={"lag": {"ticks": 2}})),
            r"rates\.lag: missing required field 'basis'",
        ),
        (
            broken(lambda d: d.update(rates={"lag": {"ticks": -1, "basis": "b"}})),
            r"rates\.lag\.ticks: must not be negative",
        ),
        (
            broken(lambda d: d.update(rates={"lag": {"ticks": 1.5, "basis": "b"}})),
            r"rates\.lag\.ticks: must be an integer",
        ),
        (
            broken(lambda d: d.update(rates={"lag": {"ticks": True, "basis": "b"}})),
            r"rates\.lag\.ticks: must be an integer",
        ),
        (
            broken(lambda d: d.update(rates={"lag": {"ticks": 1, "basis": ""}})),
            r"rates\.lag\.basis: must be a non-empty string",
        ),
        (
            broken(lambda d: d.update(rates={"bad name": {"ticks": 1, "basis": "b"}})),
            r"rates: 'bad name' is not a valid rate name",
        ),
    ],
)
def test_structural_problems_are_reported_with_their_path(data, message):
    problems = validate_snapshot(data)
    assert problems, "expected problems"
    assert any(re.search(message, p) for p in problems), problems


@pytest.mark.parametrize("confidence", ["high", "medium", "low"])
def test_a_variable_with_no_indicators_is_refused_unless_assumed(confidence):
    problems = validate_snapshot(doc(confidence=confidence, indicators=[]))
    assert len(problems) == 1
    assert re.search(r"variables\.v: no indicators, and only confidence 'assumed'", problems[0])
    assert validate_snapshot(doc(confidence="assumed", indicators=[])) == []


def test_every_problem_is_reported_not_just_the_first():
    data = doc(confidence="certain", indicators=[{"id": "i"}])
    data["date"] = "yesterday"
    problems = validate_snapshot(data)
    assert len(problems) >= 6
    assert all(re.match(r"[a-z$_]+[\w.\[\]]*: ", p) for p in problems), problems


# -- the validator agrees with the schema file -------------------------------------------------


def paths(node, prefix=()):
    """Every path into a JSON document, parents before children (the root is ``()``)."""
    yield prefix
    if isinstance(node, dict):
        for key, child in node.items():
            yield from paths(child, (*prefix, key))
    elif isinstance(node, list):
        for k, child in enumerate(node):
            yield from paths(child, (*prefix, k))


def at(node, path):
    for step in path:
        node = node[step]
    return node


def replaced(data, path, value):
    out = copy.deepcopy(data)
    if not path:
        return value
    at(out, path[:-1])[path[-1]] = value
    return out


def dropped(data, path):
    out = copy.deepcopy(data)
    container = at(out, path[:-1])
    if isinstance(container, dict):
        del container[path[-1]]
    else:
        container.pop(path[-1])
    return out


REPLACEMENTS = [
    None,
    True,
    False,
    0,
    -1,
    2.0,
    1.5,
    "",
    "x",
    "assumed",
    "2026-02-30",
    "2026-10-11",
    [],
    {},
    ["a"],
    {"a": 1},
]


def corpus():
    """The valid documents and many one-step mutations of them."""
    bases = [example(), DESIGN_EXAMPLE]
    assumed = doc(confidence="assumed", indicators=[], level=2)
    assumed["rates"] = {"lag": {"ticks": 0, "basis": "b"}}
    bases.append(assumed)
    for base in bases:
        yield base
        for path in paths(base):
            if not path:
                for value in REPLACEMENTS:
                    yield value
                continue
            yield dropped(base, path)
            for value in REPLACEMENTS:
                yield replaced(base, path, value)
            if isinstance(at(base, path), dict):
                yield replaced(base, (*path, "extra"), 1)
        for section in ("variables", "rates"):
            for name in base.get(section, {}):
                renamed = copy.deepcopy(base)
                renamed[section]["not a name"] = renamed[section].pop(name)
                yield renamed
    for confidence in ("high", "medium", "low", "assumed", "certain", None, 1):
        for indicators in ([], [indicator()]):
            yield doc(confidence=confidence, indicators=indicators)


def test_the_validator_agrees_with_the_schema_file_on_a_mutation_corpus():
    jsonschema = pytest.importorskip("jsonschema")
    validator = jsonschema.Draft202012Validator(schema(), format_checker=jsonschema.FormatChecker())
    valid = invalid = 0
    for candidate in corpus():
        theirs = sorted(e.message for e in validator.iter_errors(candidate))
        mine = validate_snapshot(candidate)
        assert bool(mine) == bool(theirs), (candidate, mine, theirs)
        valid, invalid = valid + (not mine), invalid + bool(mine)
    # The corpus is only evidence if it exercises both outcomes a lot.
    assert valid >= 50 and invalid >= 500, (valid, invalid)
