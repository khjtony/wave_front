"""scripts/compare_backends.py: a document the backend failed on is left out of the counts,
precision and recall, and reported separately."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _script():
    spec = importlib.util.spec_from_file_location(
        "compare_backends", ROOT / "scripts" / "compare_backends.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_failed_documents_are_not_counted_as_misses():
    cb = _script()
    ours = {"a": {("treaty", "intact")}}
    ref = {"a": {("treaty", "intact")}, "b": {("axis", "true"), ("rhineland", "remilitarized")}}
    report = cb.compare(ours, ref, ["a", "b"], {"b"})
    assert report["recall"] == 1.0 and report["precision"] == 1.0
    assert report["counts"] == {"match": 1}
    assert report["failed_documents"] == ["b"]
    assert report["reference_proposals_on_failed"] == 2
    # without a failure, b's pairs are misses
    plain = cb.compare(ours, ref, ["a", "b"])
    assert plain["recall"] == 1 / 3 and plain["counts"]["missing"] == 2
    assert plain["failed_documents"] == []
