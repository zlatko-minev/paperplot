"""The journal spec data types: ``FontScale`` and ``JournalSpec``.

These are pure, frozen data. The only behavior is ``figsize`` (pure geometry,
delegated to :mod:`paperplot.layout`). Styling (``rcparams``) and validation
(``preflight``) live in their own modules as free functions so this stays plain,
testable data with no matplotlib-Figure coupling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Tuple


@dataclass(frozen=True)
class FontScale:
    """Point sizes plus the APS cap-height floor."""

    base: float = 8.0       # axis labels, title, default text
    tick: float = 7.5       # tick labels
    panel: float = 9.0      # (a)(b)(c) panel letters, bold
    legend: float = 7.5
    min_warn_pt: float = 7.0          # preflight warns below this (defaults pass)
    min_cap_height_mm: float = 2.0    # APS rule (reported at info level)
    cap_height_ratio: float = 0.72    # cap-height / em for sans faces

    def cap_height_mm(self, pt: float) -> float:
        """Approximate printed cap-height of ``pt`` text, in mm."""
        return pt * (25.4 / 72.0) * self.cap_height_ratio


@dataclass(frozen=True)
class JournalSpec:
    """Immutable, queryable description of one journal's figure rules."""

    name: str
    revision: str
    widths_mm: Mapping[str, float]
    page_height_mm: float
    caption_reserve_mm: float
    font_family: Tuple[str, ...]
    font_pt: FontScale = field(default_factory=FontScale)
    min_linewidth_pt: float = 0.5
    page_body_pt: float = 10.0  # manuscript body text size (for preview_in_page)
    rasterize_dpi: Mapping[str, int] = field(
        default_factory=lambda: {"line": 600, "photo": 300}
    )

    def width_in(self, width="single") -> float:
        from . import layout

        return layout.width_in(self, width)

    def figsize(self, width="single", aspect="golden", height=None):
        from . import layout

        return layout.figsize(self, width, aspect=aspect, height=height)
