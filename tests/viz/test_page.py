"""The toy page in a real browser (docs/visualizer.md section 8): it loads without console
errors, every view draws marks, the filter row drives the status band, and the views
interact. Skipped when Playwright or its Chromium is not available."""

import glob
import os

import pytest

from wavefront.viz import render_html

pytestmark = pytest.mark.slow


def chromium_executable():
    root = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    found = sorted(glob.glob(os.path.join(root, "chromium-*", "chrome-linux*", "chrome")))
    return found[-1] if found else None


@pytest.fixture(scope="module")
def browser():
    sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed")
    exe = chromium_executable()
    if exe is None:
        pytest.skip("no pre-installed Chromium under PLAYWRIGHT_BROWSERS_PATH")
    with sync_api.sync_playwright() as p:
        try:
            b = p.chromium.launch(executable_path=exe)
        except Exception as exc:  # pragma: no cover - depends on the machine
            pytest.skip(f"Chromium cannot be launched: {exc}")
        yield b
        b.close()


@pytest.fixture(scope="module")
def toy_page(toy_bundle, tmp_path_factory):
    out = tmp_path_factory.mktemp("page") / "toy.html"
    render_html(toy_bundle, out)
    return out


def open_page(browser, path, width=1280, scheme="light"):
    ctx = browser.new_context(viewport={"width": width, "height": 900}, color_scheme=scheme)
    page = ctx.new_page()
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(path.as_uri())
    page.wait_for_selector("#board-svg")
    return ctx, page, errors


def band(page, row="trace", coalition=0):
    sel = f'#board-svg g[data-row="{row}"][data-coalition="{coalition}"]'
    return [int(x) for x in page.eval_on_selector_all(sel, "els => els.map(e => e.dataset.status)")]


def markers(page):
    return page.eval_on_selector_all(
        "#board-svg [data-marker]", "els => els.map(e => e.dataset.marker)"
    )


def test_toy_page_renders_every_view_without_errors(browser, toy_page, tmp_path):
    ctx, page, errors = open_page(browser, toy_page)
    # opens on aims = hegemonic, {INC}, TAKEOVER
    assert page.input_value("#f-hyp-0") == "hegemonic"
    assert page.input_value("#f-coal") == "0" and page.input_value("#f-ending") == "0"
    assert page.locator("#tiles .tile").count() == 5
    assert page.locator("#sec-initial table tbody tr").count() >= 6
    # status band: kept, lost, lost, failed; point of no return at tick 1, takeover at 3
    assert band(page) == [0, 2, 2, 3]
    assert {"t_K 1", "t_L 1", "t_φ 3", "⚑ TAKEOVER 3", "balance false 2"} <= set(markers(page))
    assert page.locator("#board-svg rect").count() > 20
    assert page.locator("#sec-tree .tree-row").count() >= 8
    assert page.locator("#compare-svg g[data-status]").count() >= 5
    assert "First difference at tick 1" in page.inner_text("#sec-compare")
    land = (
        page.locator("#sec-landscape canvas").count()
        + page.locator("#landscape-svg circle").count()
    )
    assert land > 0
    assert page.locator("#sec-tables table tbody tr").count() > 10
    page.screenshot(path=str(tmp_path / "toy_page.png"), full_page=True)
    assert (tmp_path / "toy_page.png").stat().st_size > 10_000
    assert errors == []
    ctx.close()


def test_filter_row_drives_the_status_band(browser, toy_page):
    ctx, page, errors = open_page(browser, toy_page)
    before = band(page)
    # the property: balance instead of "not TAKEOVER" recolors the cells
    page.select_option("#f-prop", label="balance")
    assert band(page) != before and band(page)[-1] == 3
    assert "t_K 0" in markers(page)
    page.select_option("#f-prop", value="auto")
    assert band(page) == before
    # the coalition moves the markers: {CH} alone keeps "not TAKEOVER" throughout
    page.select_option("#f-coal", label="{CH}")
    assert band(page, coalition=1)[0] == 0
    assert "t_K 1" not in markers(page)
    # the hypothesis: no takeover from limited aims
    page.select_option("#f-hyp-0", "limited")
    assert page.locator("#board-svg").count() == 0
    assert "No play reaches TAKEOVER" in page.inner_text("#sec-board")
    assert errors == []
    ctx.close()


def test_decision_tree_builds_a_branch_with_a_fork(browser, toy_page):
    ctx, page, errors = open_page(browser, toy_page)
    rows = page.inner_text("#sec-tree")
    assert "resist" in rows and "concede" in rows
    # at tick 0 INC resists instead of idling: the branch stays kept where the trace is lost
    page.click("#tree-1-2")
    page.click("#tree-step")
    assert band(page, row="branch") == [0, 0]
    assert any(m.startswith("fork") for m in markers(page))
    assert "Fork at tick 1" in page.inner_text("#sec-tree")
    assert page.input_value("#f-compare") == "cf"
    page.click("#tree-reset")
    assert band(page, row="branch") == []
    # keyboard: the board selects ticks with the arrow keys
    page.focus("#board-svg")
    page.keyboard.press("ArrowRight")
    assert "From tick 1" in page.inner_text("#sec-tree")
    assert errors == []
    ctx.close()


def test_table_twins_theme_and_narrow_layout(browser, toy_page):
    ctx, page, errors = open_page(browser, toy_page, width=390, scheme="dark")
    assert page.evaluate("document.documentElement.scrollWidth") <= 390
    bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
    page.click("#theme-light")
    assert page.evaluate("document.documentElement.dataset.theme") == "light"
    assert page.evaluate("getComputedStyle(document.body).backgroundColor") != bg
    page.click("#all-tables")
    for sec in ("initial", "board", "tree", "compare", "landscape"):
        assert page.locator(f"#sec-{sec} table").count() >= 1, sec
    assert "TAKEOVER" in page.inner_text("#sec-board table")
    assert page.evaluate("document.documentElement.scrollWidth") <= 390
    assert errors == []
    ctx.close()


def test_landscape_hover_shows_the_nearest_state(browser, toy_page):
    ctx, page, errors = open_page(browser, toy_page)
    page.locator("#landscape-svg").scroll_into_view_if_needed()
    box = page.locator("#landscape-svg").bounding_box()
    # the trace's second marker (tick 1); hovering 8px off it still finds a state
    cx, cy = page.eval_on_selector_all(
        '#landscape-svg circle[r="4"]',
        "els => [+els[1].getAttribute('cx'), +els[1].getAttribute('cy')]",
    )
    page.mouse.move(box["x"] + cx + 6, box["y"] + cy + 5)
    tip = page.locator("#sec-landscape .tip")
    assert tip.is_visible()
    assert "tick 1" in tip.inner_text() and "state #" in tip.inner_text()
    page.click("#lmode-backward")
    page.click("#lmode-forward")
    assert errors == []
    ctx.close()
