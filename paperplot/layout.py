"""Figure geometry: width classes, unit conversions, and figsize math.

Pure geometry — no matplotlib styling here. ``units`` live here too (the
conversions are small and only used for sizing).
"""

from __future__ import annotations

import difflib
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # avoid a runtime import cycle with journals.py
    from .journals import JournalSpec

MM_PER_IN = 25.4
GOLDEN = (1.0 + 5.0 ** 0.5) / 2.0  # ~1.618


def mm_to_in(mm: float) -> float:
    return mm / MM_PER_IN


def in_to_mm(inch: float) -> float:
    return inch * MM_PER_IN


def pt_to_mm(pt: float) -> float:
    return pt * (MM_PER_IN / 72.0)  # 1 pt = 1/72 in


class Width(str, Enum):
    """Standard journal figure widths."""

    SINGLE = "single"
    ONEHALF = "onehalf"
    DOUBLE = "double"
    FULL_PAGE = "full_page"


def resolve_width(width) -> str:
    """Normalize a Width/str to a canonical key, with a friendly error."""
    if isinstance(width, Width):
        return width.value
    key = str(width).strip().lower().replace("-", "_")
    valid = [w.value for w in Width]
    if key in valid:
        return key
    hint = difflib.get_close_matches(key, valid, n=1)
    suffix = f" Did you mean {hint[0]!r}?" if hint else ""
    raise ValueError(f"Unknown width {width!r}. Valid: {valid}.{suffix}")


def width_in(spec: "JournalSpec", width="single") -> float:
    """Physical figure width in inches for the given width class."""
    key = resolve_width(width)
    if key == Width.FULL_PAGE.value:
        key = Width.DOUBLE.value  # full-page spans the double-column block
    try:
        return mm_to_in(spec.widths_mm[key])
    except KeyError:
        raise ValueError(
            f"Journal {spec.name!r} has no {key!r} width "
            f"(has {sorted(spec.widths_mm)})."
        ) from None


def figsize(spec: "JournalSpec", width="single", aspect="golden", height=None):
    """Return ``(w_in, h_in)``.

    Width is fixed by the column class. Height comes from ``height`` (inches,
    overrides everything), else ``aspect`` applied to the width, clamped to the
    page's usable height. ``FULL_PAGE`` defaults to page-height minus the caption
    reserve so it actually fills the page.
    """
    key = resolve_width(width)
    w = width_in(spec, key)
    usable_h = mm_to_in(spec.page_height_mm)

    if key == Width.FULL_PAGE.value:
        if height is not None:
            h = float(height)
        else:
            h = mm_to_in(spec.page_height_mm - spec.caption_reserve_mm)
        return (w, min(h, usable_h))

    if height is not None:
        h = float(height)
    elif aspect in (None, "golden"):
        h = w / GOLDEN
    elif aspect == "equal":
        h = w
    else:
        h = w * float(aspect)  # aspect = height / width

    return (w, min(h, usable_h))
