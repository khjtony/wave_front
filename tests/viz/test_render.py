"""The rendered page: one self-contained file with the bundle embedded."""

import importlib
import json
import re

import pytest

from tests.analysis.games import crisis
from wavefront.model import Model, V
from wavefront.report import CAVEAT
from wavefront.viz import MAX_PAGE_BYTES, PageTooLarge, bundle, render, render_html

render_module = importlib.import_module("wavefront.viz.render")


def embedded(text):
    m = re.search(r'<script type="application/json" id="bundle">(.*?)</script>', text, re.S)
    assert m, "the bundle script element is missing"
    return json.loads(m.group(1))


@pytest.fixture(scope="module")
def toy_page(toy_bundle, tmp_path_factory):
    out = tmp_path_factory.mktemp("viz") / "toy.html"
    render_html(toy_bundle, out)
    return out


def test_toy_page_is_self_contained_and_small(toy_page, toy_bundle):
    text = toy_page.read_text(encoding="utf-8")
    assert "http" not in text  # no URL at all, not even the SVG namespace
    assert not re.search(r"<(script|link|img|iframe)[^>]*\s(src|href)=", text)
    assert "@import" not in text and "url(" not in text
    assert toy_page.stat().st_size < MAX_PAGE_BYTES
    assert toy_page.stat().st_size < 4_000_000
    assert CAVEAT in json.dumps(embedded(text), ensure_ascii=False)
    assert embedded(text) == toy_bundle
    assert "<title>two_power visualizer</title>" in text
    assert text.count("<script") == 2  # the bundle and the inlined script


def test_strings_from_the_model_cannot_close_the_script_element(tmp_path):
    evil = "</script><script>alert(1)</script><!-- &  "
    m = Model("evil", horizon=2, description=evil)
    m.counter("x", max=2)
    a = m.actor("A")
    a.action("go", guard=V.x < 2, effect=[], source=evil)
    m.ending("END", V.x == 2)
    data = bundle(m, max_relax=0)
    out = render_html(data, tmp_path / "evil.html")
    text = out.read_text(encoding="utf-8")
    assert text.count("</script>") == 2
    assert "alert(1)</script>" not in text
    assert embedded(text)["meta"]["description"] == evil


def test_title_is_escaped(tmp_path):
    m = Model("a<b>&c", horizon=1)
    m.flag("f")
    m.actor("A")
    out = render_html(bundle(m, max_relax=0), tmp_path / "t.html")
    assert "<title>a&lt;b&gt;&amp;c visualizer</title>" in out.read_text(encoding="utf-8")


def test_render_writes_the_page_and_creates_directories(tmp_path):
    out = render(crisis(), tmp_path / "sub" / "crisis.html", max_relax=0)
    assert out.exists() and embedded(out.read_text(encoding="utf-8"))["meta"]["name"] == "crisis"


def test_page_size_limit(tmp_path, monkeypatch):
    data = bundle(crisis(), max_relax=0)
    monkeypatch.setattr(render_module, "MAX_PAGE_BYTES", 1000)
    with pytest.raises(PageTooLarge, match="16 MB"):
        render_html(data, tmp_path / "big.html")
    assert not (tmp_path / "big.html").exists()


def test_templates_are_package_data():
    from importlib import resources

    root = resources.files("wavefront.viz").joinpath("template")
    for name in ("index.html", "viz.css", "viz.js"):
        assert root.joinpath(name).is_file()
    js = root.joinpath("viz.js").read_text(encoding="utf-8")
    assert "innerHTML" not in js and "insertAdjacentHTML" not in js and "eval(" not in js
