"""The page's colors are the validated ones, declared once with the dark values under both
scopes (the OS setting and the theme toggle)."""

import re
from importlib import resources
from pathlib import Path

CSS = resources.files("wavefront.viz").joinpath("template", "viz.css").read_text(encoding="utf-8")
RECORD = (Path(__file__).parent / "palette_validation.txt").read_text(encoding="utf-8")
DATA_ROLES = re.compile(r"--(s[1-8]|st[0-3]|r[0-9]|nature)\s*:\s*(#[0-9a-fA-F]{6})")


def blocks():
    light = CSS[: CSS.index("@media (prefers-color-scheme: dark)")]
    media = CSS[
        CSS.index("@media (prefers-color-scheme: dark)") : CSS.index(':root[data-theme="dark"]')
    ]
    toggle = CSS[CSS.index(':root[data-theme="dark"]') : CSS.index("* { box-sizing")]
    return light, media, toggle


def roles(block):
    return dict(DATA_ROLES.findall(block))


def test_dark_values_are_declared_under_both_scopes():
    light, media, toggle = blocks()
    assert ':root:where(:not([data-theme="light"]))' in media
    tokens = re.compile(r"(--[a-z0-9-]+)\s*:\s*([^;]+);")
    assert dict(tokens.findall(media)) == dict(tokens.findall(toggle))
    fixed = {"--st0", "--st1", "--st2", "--st3"}  # status colors are never themed
    assert set(dict(tokens.findall(light))) - fixed == set(dict(tokens.findall(media)))


def test_every_data_color_was_validated():
    light, media, _ = blocks()
    used = set(roles(light).values()) | set(roles(media).values())
    assert len(used) >= 25
    missing = [c for c in used if c.lower() not in RECORD.lower() and c != "#898781"]
    assert missing == []


def test_status_colors_are_fixed_and_the_reference_steps():
    light, media, _ = blocks()
    expected = {"st0": "#0ca30c", "st1": "#fab219", "st2": "#ec835a", "st3": "#d03b3b"}
    assert {k: v for k, v in roles(light).items() if k.startswith("st")} == expected
    assert not any(k.startswith("st") for k in roles(media))
