"""The visualizer (docs/visualizer.md): one self-contained HTML page per model.

:func:`bundle` computes every number the page shows from the engine and the analysis layer;
:func:`render_html` writes the page for a bundle; :func:`render` does both. The page only
draws: it has no engine of its own.
"""

from .bundle import DECISION_NAMES, STATUS_NAMES, bundle, decision_classes, replay, status_codes
from .format import expr_text
from .render import MAX_PAGE_BYTES, PageTooLarge, render, render_html

__all__ = [
    "bundle",
    "render",
    "render_html",
    "expr_text",
    "status_codes",
    "decision_classes",
    "replay",
    "STATUS_NAMES",
    "DECISION_NAMES",
    "MAX_PAGE_BYTES",
    "PageTooLarge",
]
