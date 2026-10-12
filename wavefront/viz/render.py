"""Write the visualizer page: one HTML file with the CSS, the JS and the bundle inlined."""

from __future__ import annotations

import html
import json
from importlib import resources
from pathlib import Path
from typing import Any

from ..model.model import Model

__all__ = ["render_html", "render", "page_html", "MAX_PAGE_BYTES", "PageTooLarge"]

MAX_PAGE_BYTES = 16 * 1024 * 1024


class PageTooLarge(ValueError):
    """The rendered page would exceed :data:`MAX_PAGE_BYTES`."""


def _template(name: str) -> str:
    return resources.files("wavefront.viz").joinpath("template", name).read_text(encoding="utf-8")


def _json_for_script(data: Any) -> str:
    """JSON safe inside ``<script type="application/json">``: every ``<`` is escaped (so no
    ``</script>`` or ``<!--`` can end or alter the element), as are U+2028/U+2029."""
    text = json.dumps(data, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return (
        text.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace(" ", "\\u2028")
        .replace(" ", "\\u2029")
    )


def page_html(data: dict[str, Any]) -> str:
    """The page for a bundle, as a string."""
    page = _template("index.html")
    parts = {
        "__VIZ_TITLE__": html.escape(f"{data['meta']['name']} visualizer"),
        "/*__VIZ_CSS__*/": _template("viz.css"),
        "/*__VIZ_JS__*/": _template("viz.js"),
        "__VIZ_BUNDLE__": _json_for_script(data),
    }
    for key, value in parts.items():
        if key not in page:
            raise RuntimeError(f"template is missing the placeholder {key}")
        page = page.replace(key, value)
    return page


def render_html(data: dict[str, Any], out_path: str | Path) -> Path:
    """Write the page for bundle ``data`` to ``out_path`` and return the path. Raises
    :class:`PageTooLarge` if the page would exceed 16 MB (lower ``max_moves``)."""
    text = page_html(data)
    size = len(text.encode("utf-8"))
    if size > MAX_PAGE_BYTES:
        raise PageTooLarge(
            f"the page would be {size / 1e6:.1f} MB, above the 16 MB limit; "
            "lower max_moves so that only the shown traces' neighborhood is included"
        )
    out = Path(out_path)
    if out.parent and not out.parent.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out


def render(model: Model, out_path: str | Path, **bundle_kwargs: Any) -> Path:
    """Compute the bundle of ``model`` (keyword arguments as :func:`wavefront.viz.bundle`)
    and write its page to ``out_path``."""
    from .bundle import bundle

    return render_html(bundle(model, **bundle_kwargs), out_path)
