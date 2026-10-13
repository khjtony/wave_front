"""Snapshots: a dated state estimate with provenance (spec section 9, DESIGN.md section 5.1).

Real-world evidence enters the framework in exactly two places: the current state estimate
and the rates. A snapshot file carries both, with the indicators each level was read from::

    {
      "date": "2026-10-11",
      "model": "two_power",
      "variables": {
        "oversight": {
          "level": "weak",
          "confidence": "medium",
          "indicators": [
            {"id": "audit_regime", "value": "...", "source": "<url>",
             "observed": "2026-09-30", "rule": "reports without verification -> weak"}
          ]
        }
      },
      "builtins": {
        "pending_INC_fund_oversight": {
          "value": 1, "confidence": "medium",
          "indicators": [{"id": "budget_2026", "value": "...", "source": "<url>",
                          "observed": "2026-07-01", "rule": "programme funded in 2026Q3"}],
          "rule": "decided in 2026Q3 with delay 2: 2 - (2026Q4 - 2026Q3) = 1"
        }
      },
      "rates": {"fund_oversight": {"ticks": 2, "basis": "..."}}
    }

The format is fixed by ``snapshots/schema.json`` (JSON Schema draft 2020-12). This module
checks it with a small hand-written validator for exactly that schema, so that the core keeps
no third-party dependency; ``tests/evidence`` cross-checks the two against each other.

Three layers, each usable on its own:

* :func:`validate_snapshot` checks structure and provenance and returns the list of
  problems (empty when the snapshot is valid). It needs no model.
* :func:`snapshot_to_state` maps a validated snapshot onto a compiled model's variables and
  returns the state tuple.
* :func:`load_snapshot` reads a file and does both.

The mapping is deliberately strict. Level variables are given by level *name*, counters by
integer and flags by boolean. A variable the snapshot does not mention takes its declared
initial value, except that a variable declared with ``init=None`` (a swept hidden objective or
parameter) has no such value, so the snapshot must fix it; pin a hypothesis with
``confidence: "assumed"``.

Built-in variables cannot be set in ``variables``. The optional ``builtins`` section
(phase 2 decision F2) sets them, each with a ``value``, a ``confidence``, ``indicators`` and
the ``rule`` that derives the value: ``pending_<actor>_<action>`` takes the ticks remaining
until the delayed effect applies (an integer from 0 to the action's delay),
``last_<actor>`` an action name of that actor or ``none``, a latch one of its levels or
``unset`` (a boolean for a latch of a flag, an integer for a latch of the tick), and
``fair_<name>`` its count (0 to the constraint's ``within``). They are filled in after the
variables. ``tick`` is not settable: a snapshot is dated, and the caller maps the date to a
tick. Built-ins a snapshot omits keep their initial values, and a latch the snapshot omits
is set, when its condition already holds in the loaded state, to the loaded value of the
variable it copies, exactly as for the model's own initial states. A latch given as
``unset`` although its condition holds in the loaded state is refused: no play of the model
reaches such a state.

The returned state is not filtered by the model's ``assume`` restrictions (spec 3.1a): a
snapshot is evidence about where the world is, so it may lie outside what the model assumes,
and ``explore(cm, initial=[state])`` takes it as given. The ``model`` field and the ``rates``
are checked for shape but neither compared with the compiled model nor applied to it: rates
are evidence for reviewing the model's parameters, never an edit of its transition relation.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from datetime import date as _date
from pathlib import Path
from typing import Any

from ..model.compile import CompiledModel, VarSpec
from ..model.model import ModelError

__all__ = [
    "SnapshotError",
    "CONFIDENCE_LEVELS",
    "validate_snapshot",
    "snapshot_to_state",
    "read_snapshot",
    "load_snapshot",
]

CONFIDENCE_LEVELS = ("high", "medium", "low", "assumed")
ASSUMED = "assumed"

_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

_TOP_REQUIRED = ("date", "model", "variables")
_TOP_ALLOWED = (*_TOP_REQUIRED, "builtins", "rates", "$schema")
_VARIABLE_FIELDS = ("level", "confidence", "indicators")
_BUILTIN_FIELDS = ("value", "confidence", "indicators", "rule")
_INDICATOR_FIELDS = ("id", "value", "source", "observed", "rule")
_RATE_FIELDS = ("ticks", "basis")


class SnapshotError(ModelError):
    """A snapshot that is malformed, lacks provenance or does not fit the model.

    It is a :class:`~wavefront.model.ModelError` (and so a ``ValueError``): a snapshot the
    model cannot take is a user error of the same kind as a bad model, and the ``wf`` command
    reports it with the same exit code. ``problems`` lists every individual problem found;
    ``str(error)`` joins them."""

    def __init__(self, message: str, problems: list[str] | None = None) -> None:
        super().__init__(message)
        self.problems = list(problems) if problems is not None else [message]


# -- structural validation ------------------------------------------------------------------


def _is_int(value: object) -> bool:
    """A JSON integer: ``bool`` is excluded, and ``3.0`` counts as one (as in JSON Schema)."""
    if isinstance(value, bool):
        return False
    return isinstance(value, int) or (isinstance(value, float) and value.is_integer())


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _is_text(value: object) -> bool:
    return isinstance(value, str) and value != ""


def _object(
    obj: object,
    path: str,
    required: tuple[str, ...],
    allowed: tuple[str, ...],
    problems: list[str],
) -> dict[str, Any] | None:
    """``obj`` if it is an object; reports missing required and unexpected fields."""
    if not isinstance(obj, dict):
        problems.append(f"{path}: must be an object")
        return None
    for key in required:
        if key not in obj:
            problems.append(f"{path}: missing required field {key!r}")
    for key in obj:
        if key not in allowed:
            problems.append(f"{path}: unexpected field {key!r}")
    return obj


def _check_date(value: object, path: str, problems: list[str]) -> None:
    if not isinstance(value, str) or not _DATE.fullmatch(value):
        problems.append(f"{path}: {value!r} is not a date in YYYY-MM-DD form")
        return
    try:
        _date.fromisoformat(value)
    except ValueError:
        problems.append(f"{path}: {value!r} is not a calendar date")


def _check_indicator(entry: object, path: str, problems: list[str]) -> None:
    ind = _object(entry, path, _INDICATOR_FIELDS, _INDICATOR_FIELDS, problems)
    if ind is None:
        return
    for key in ("id", "source", "rule"):
        if key in ind and not _is_text(ind[key]):
            problems.append(f"{path}.{key}: must be a non-empty string")
    if "value" in ind:
        value = ind["value"]
        if isinstance(value, str):
            if value == "":
                problems.append(f"{path}.value: must not be an empty string")
        elif not (isinstance(value, bool) or _is_number(value)):
            problems.append(f"{path}.value: must be a string, number or boolean, not {value!r}")
    if "observed" in ind:
        _check_date(ind["observed"], f"{path}.observed", problems)


def _check_variable(name: str, entry: object, problems: list[str]) -> None:
    path = f"variables.{name}"
    if not _NAME.fullmatch(name):
        problems.append(f"variables: {name!r} is not a valid variable name")
    var = _object(entry, path, _VARIABLE_FIELDS, _VARIABLE_FIELDS, problems)
    if var is None:
        return
    if "level" in var:
        level = var["level"]
        if not (isinstance(level, str | bool) or _is_int(level)):
            problems.append(f"{path}.level: must be a level name, an integer or a boolean")
        elif level == "":
            problems.append(f"{path}.level: must not be an empty string")
    _check_provenance(path, var, problems)


def _check_provenance(path: str, var: dict[str, Any], problems: list[str]) -> None:
    """The ``confidence`` and ``indicators`` of a variable or built-in entry."""
    confidence = var.get("confidence")
    if "confidence" in var and not (
        isinstance(confidence, str) and confidence in CONFIDENCE_LEVELS
    ):
        problems.append(
            f"{path}.confidence: {confidence!r} is not one of {', '.join(CONFIDENCE_LEVELS)}"
        )
    if "indicators" not in var:
        return
    indicators = var["indicators"]
    if not isinstance(indicators, list):
        problems.append(f"{path}.indicators: must be an array")
        return
    for k, indicator in enumerate(indicators):
        _check_indicator(indicator, f"{path}.indicators[{k}]", problems)
    if not indicators and "confidence" in var and confidence != ASSUMED:
        problems.append(
            f"{path}: no indicators, and only confidence {ASSUMED!r} may omit them "
            f"(confidence is {confidence!r})"
        )


def _check_builtin(name: str, entry: object, problems: list[str]) -> None:
    path = f"builtins.{name}"
    if not _NAME.fullmatch(name):
        problems.append(f"builtins: {name!r} is not a valid built-in name")
    var = _object(entry, path, _BUILTIN_FIELDS, _BUILTIN_FIELDS, problems)
    if var is None:
        return
    if "value" in var:
        value = var["value"]
        if isinstance(value, str):
            if value == "":
                problems.append(f"{path}.value: must not be an empty string")
        elif isinstance(value, bool):
            pass
        elif not _is_int(value):
            problems.append(
                f"{path}.value: must be a non-negative integer, a name or a boolean, not {value!r}"
            )
        elif value < 0:
            problems.append(f"{path}.value: must not be negative, not {value!r}")
    if "rule" in var and not _is_text(var["rule"]):
        problems.append(f"{path}.rule: must be a non-empty string")
    _check_provenance(path, var, problems)


def _check_rate(name: str, entry: object, problems: list[str]) -> None:
    path = f"rates.{name}"
    if not _NAME.fullmatch(name):
        problems.append(f"rates: {name!r} is not a valid rate name")
    rate = _object(entry, path, _RATE_FIELDS, _RATE_FIELDS, problems)
    if rate is None:
        return
    if "ticks" in rate:
        ticks = rate["ticks"]
        if not _is_int(ticks):
            problems.append(f"{path}.ticks: must be an integer, not {ticks!r}")
        elif ticks < 0:
            problems.append(f"{path}.ticks: must not be negative, not {ticks!r}")
    if "basis" in rate and not _is_text(rate["basis"]):
        problems.append(f"{path}.basis: must be a non-empty string")


def validate_snapshot(data: object) -> list[str]:
    """Check ``data`` (a parsed snapshot) against ``snapshots/schema.json``.

    Returns the problems found, each prefixed with the path of the offending field; the list
    is empty exactly when the snapshot is valid. This includes the provenance rule: every
    variable and every built-in lists at least one indicator unless its confidence is
    ``"assumed"``. It does not look at any model; :func:`snapshot_to_state` does."""
    problems: list[str] = []
    top = _object(data, "snapshot", _TOP_REQUIRED, _TOP_ALLOWED, problems)
    if top is None:
        return problems
    if "$schema" in top and not isinstance(top["$schema"], str):
        problems.append("snapshot.$schema: must be a string")
    if "date" in top:
        _check_date(top["date"], "date", problems)
    if "model" in top and not _is_text(top["model"]):
        problems.append("model: must be a non-empty string")
    if "variables" in top:
        variables = top["variables"]
        if isinstance(variables, dict):
            for name, entry in variables.items():
                _check_variable(str(name), entry, problems)
        else:
            problems.append("variables: must be an object")
    if "builtins" in top:
        builtins = top["builtins"]
        if isinstance(builtins, dict):
            for name, entry in builtins.items():
                _check_builtin(str(name), entry, problems)
        else:
            problems.append("builtins: must be an object")
    if "rates" in top:
        rates = top["rates"]
        if isinstance(rates, dict):
            for name, entry in rates.items():
                _check_rate(str(name), entry, problems)
        else:
            problems.append("rates: must be an object")
    return problems


# -- mapping onto a compiled model ------------------------------------------------------------


def _level_value(spec: VarSpec, level: object) -> tuple[int, None] | tuple[None, str]:
    """The state value for ``level`` of a declared variable, or a message saying why not."""
    if spec.kind == "level":
        if isinstance(level, str) and level in spec.levels:
            return spec.levels.index(level), None
        return None, (
            f"variable {spec.name!r} has no level {level!r} (levels: {', '.join(spec.levels)})"
        )
    if spec.kind == "counter":
        if isinstance(level, int | float) and _is_int(level) and 0 <= level < spec.size:
            return int(level), None
        return None, (
            f"variable {spec.name!r} is a counter 0..{spec.size - 1}, "
            f"so level {level!r} is not an integer in that range"
        )
    if isinstance(level, bool):
        return int(level), None
    return None, f"variable {spec.name!r} is a flag, so level {level!r} is not true or false"


def _settable_builtins(cm: CompiledModel) -> dict[str, tuple[VarSpec, str]]:
    """The built-ins a snapshot may set, with a description of each one's range."""
    out: dict[str, tuple[VarSpec, str]] = {}
    delayed = {
        f"pending_{actor.name}_{a.name}": f"{actor.name}.{a.name}"
        for actor in cm.actors
        for a in actor.actions
        if a.delay
    }
    for spec in cm.variables:
        if spec.origin == "pending":
            what = delayed.get(spec.name, spec.name)
            out[spec.name] = (spec, f"the delay of {what} is {spec.size - 1}")
        elif spec.origin == "fair":
            out[spec.name] = (spec, f"its 'within' is {spec.size - 1}")
        elif spec.origin in ("last", "latch"):
            out[spec.name] = (spec, f"levels: {', '.join(spec.levels)}")
    return out


def _builtin_value(cm: CompiledModel, spec: VarSpec, rng: str, value: object) -> int | str:
    """The state value for a built-in entry's ``value``, or a message saying why not."""
    name = spec.name
    if spec.origin in ("pending", "fair"):
        counter = "pending counter" if spec.origin == "pending" else "fairness counter"
        if not _is_int(value) or isinstance(value, str):
            return f"built-in {name!r} is a {counter}, so {value!r} is not an integer"
        n = int(value)  # type: ignore[arg-type]
        if not 0 <= n < spec.size:
            return f"built-in {name!r} is {n}, outside 0..{spec.size - 1} ({rng})"
        return n
    if spec.origin == "last":
        if isinstance(value, str) and value in spec.levels:
            return spec.levels.index(value)
        return f"built-in {name!r} has no action {value!r} ({rng})"
    # a latch: 'unset', or a level of the variable it copies, given as that variable is
    latch = next(d for d in cm.model.latches if d.name == name)
    source = cm.variables[cm.index[latch.of]]
    if value == "unset" and isinstance(value, str):
        return 0
    if latch.of == "tick" or source.kind == "counter":
        ok = _is_int(value) and not isinstance(value, str)
        text = str(int(value)) if ok else None  # type: ignore[arg-type]
    elif source.kind == "flag":
        ok = isinstance(value, bool)
        text = str(value) if ok else None
    else:
        ok = isinstance(value, str)
        text = value if ok else None  # type: ignore[assignment]
    if ok and text in spec.levels:
        return spec.levels.index(text)
    return f"built-in {name!r} (a latch of {latch.of!r}) has no level {value!r} ({rng})"


def _fill_builtins(
    cm: CompiledModel, given: Mapping[str, Mapping[str, Any]], problems: list[str]
) -> dict[str, int]:
    settable = _settable_builtins(cm)
    values: dict[str, int] = {}
    for name, entry in given.items():
        value = entry["value"]
        if name not in settable:
            if name == "tick":
                why = "it is not settable: the caller maps the snapshot's date to a tick"
            elif name in cm.index:
                why = "it is a declared variable; set it in the snapshot's variables"
            else:
                names = ", ".join(settable) or "none"
                why = f"not a built-in of model {cm.name!r} (built-ins: {names})"
            problems.append(f"snapshot built-in {name!r} (value {value!r}): {why}")
            continue
        spec, rng = settable[name]
        result = _builtin_value(cm, spec, rng, value)
        if isinstance(result, str):
            problems.append(result)
        else:
            values[name] = result
    return values


def snapshot_to_state(data: dict[str, Any], cm: CompiledModel) -> tuple[int, ...]:
    """Map a snapshot onto a state of ``cm``: one value per variable, in state order.

    ``data`` is validated first (:func:`validate_snapshot`). Then every variable in the
    snapshot must be a declared variable of the model with a level of the right kind;
    variables the snapshot omits take their declared initial value, except those declared
    with ``init=None``, which the snapshot must fix. The ``builtins`` section, if any, is
    filled in after the variables: each name must be a settable built-in of the model
    (``pending_*``, ``last_*``, a latch, ``fair_*``) and each value in its range (a pending
    counter at most the action's delay). Raises :class:`SnapshotError` naming the variable
    or built-in and the value of every problem found."""
    problems = validate_snapshot(data)
    if problems:
        raise SnapshotError("invalid snapshot: " + "; ".join(problems), problems)
    declared = {v.name: v for v in cm.variables if v.origin == "var"}
    given: Mapping[str, Mapping[str, Any]] = data["variables"]
    values: dict[str, int] = {}
    for name, entry in given.items():
        level = entry["level"]
        spec = declared.get(name)
        if spec is None:
            kind = "a built-in of" if name in cm.index else "not a variable of"
            hint = (
                "a snapshot's variables set declared variables only; built-ins go in its "
                "builtins section"
                if name in cm.index
                else f"variables: {', '.join(declared)}"
            )
            problems.append(
                f"snapshot variable {name!r} (level {level!r}) is {kind} model {cm.name!r} ({hint})"
            )
            continue
        value, problem = _level_value(spec, level)
        if problem is not None:
            problems.append(problem)
        elif value is not None:
            values[name] = value
    for spec in declared.values():
        if spec.name in given:
            continue
        if len(spec.init) > 1:
            problems.append(
                f"variable {spec.name!r} has no declared initial value (it is swept over every "
                f"level: {', '.join(spec.levels)}), so the snapshot must fix it"
            )
        else:
            values[spec.name] = spec.init[0]
    builtins: Mapping[str, Mapping[str, Any]] = data.get("builtins", {})
    values.update(_fill_builtins(cm, builtins, problems))
    if problems:
        raise SnapshotError("; ".join(problems), problems)
    state = [values.get(spec.name, spec.init[0]) for spec in cm.variables]
    for latch in cm.model.latches:
        i = cm.index[latch.name]
        if state[i] != 0 or not cm.evaluate(latch.when, state):
            continue
        if latch.name in builtins:
            problems.append(
                f"built-in {latch.name!r} is given as 'unset', but its condition already "
                "holds in the loaded state, so the latch would have been set"
            )
        else:
            state[i] = state[cm.index[latch.of]] + 1
    if problems:
        raise SnapshotError("; ".join(problems), problems)
    return tuple(state)


# -- files ----------------------------------------------------------------------------------


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """``json`` keeps the last of two equal keys; in a file of evidence that would silently
    drop a variable or an indicator, so a duplicate is an error."""
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise SnapshotError(f"duplicate key {key!r} in a JSON object")
        out[key] = value
    return out


def read_snapshot(path: str | Path) -> dict[str, Any]:
    """Parse and validate a snapshot file. Raises :class:`SnapshotError` for invalid JSON, a
    duplicated key or an invalid snapshot; an unreadable file raises :class:`OSError` as
    usual."""
    path = Path(path)
    try:
        data = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SnapshotError(f"{path}: not valid JSON: {exc}") from exc
    except SnapshotError as exc:
        raise SnapshotError(f"{path}: {exc}") from None
    problems = validate_snapshot(data)
    if problems:
        raise SnapshotError(f"{path}: invalid snapshot: " + "; ".join(problems), problems)
    return data


def load_snapshot(path: str | Path, cm: CompiledModel) -> tuple[int, ...]:
    """Read a snapshot file and map it onto a state of ``cm`` (see :func:`snapshot_to_state`).

    Raises :class:`SnapshotError` if the file is not valid JSON, does not satisfy the
    schema (including the provenance rule), or does not fit the model: an unknown variable,
    an unknown level, a swept variable the snapshot leaves unfixed, or a built-in that is
    unknown, set in ``variables`` or out of range. The message names the file, the variable
    or built-in and the value."""
    data = read_snapshot(path)
    try:
        return snapshot_to_state(data, cm)
    except SnapshotError as exc:
        raise SnapshotError(f"{path}: {exc}", exc.problems) from None
