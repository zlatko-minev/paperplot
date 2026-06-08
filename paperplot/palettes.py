"""Colors: a colorblind-safe qualitative cycle, sequential/diverging colormaps,
and a small custom-palette registry. matplotlib-only (no seaborn).

The core rule: qualitative cycles (for categories) and sequential/diverging
colormaps (for ordered data) are *different things*. Using a sequential scheme
as a categorical cycle is an enforced anti-pattern, not just a docstring note.
"""

from __future__ import annotations

import warnings
from typing import Dict, List, Sequence

import matplotlib.colors as mcolors
from matplotlib import colormaps

# Okabe-Ito colorblind-safe qualitative palette (default cycle).
OKABE_ITO: List[str] = [
    "#0072B2",  # blue
    "#D55E00",  # vermillion
    "#009E73",  # green
    "#CC79A7",  # reddish purple
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#F0E442",  # yellow
    "#000000",  # black
]

# Seaborn's qualitative palettes, hardcoded so they're available without seaborn.
# The pairing that matters: MUTED for area/histogram *fills*, BRIGHT for *strokes*
# (lines, reference markers). Muted fills under bright strokes keeps overlapping
# filled shapes legible. See pp.fills() / pp.strokes().
MUTED: List[str] = [
    "#4878D0", "#EE854A", "#6ACC64", "#D65F5F", "#956CB4",
    "#8C613C", "#DC7EC0", "#797979", "#D5BB67", "#82C6E2",
]
BRIGHT: List[str] = [
    "#023EFF", "#FF7C00", "#1AC938", "#E8000B", "#8B2BE2",
    "#9F4800", "#F14CC1", "#A3A3A3", "#FFC400", "#00D7FF",
]
DEEP: List[str] = [
    "#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3",
    "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD",
]
COLORBLIND: List[str] = [
    "#0173B2", "#DE8F05", "#029E73", "#D55E00", "#CC78BC",
    "#CA9161", "#FBAFE4", "#949494", "#ECE133", "#56B4E9",
]
PASTEL: List[str] = [
    "#A1C9F4", "#FFB482", "#8DE5A1", "#FF9F9B", "#D0BBFF",
    "#DEBB9B", "#FAB0E4", "#CFCFCF", "#FFFEA3", "#B9F2F0",
]
DARK: List[str] = [
    "#001C7F", "#B1400D", "#12711C", "#8C0800", "#591E71",
    "#592F0D", "#A23582", "#3C3C3C", "#B8850A", "#006374",
]

# Named categorical palettes resolvable by pp.palette("name").
_BUILTIN: Dict[str, List[str]] = {
    "muted": MUTED,
    "bright": BRIGHT,
    "deep": DEEP,
    "colorblind": COLORBLIND,
    "pastel": PASTEL,
    "dark": DARK,
}

# Palettes designed to stay distinguishable under common color-vision deficiencies.
# The seaborn "muted"/"bright"/etc. families are NOT in this set — they pair well
# as fills/strokes but should not carry meaning across categorical *lines*.
_CB_SAFE = {"okabe-ito", "colorblind"}

# ColorBrewer + perceptual maps that are NOT valid categorical cycles.
_SEQUENTIAL = {
    "Blues", "BuGn", "BuPu", "GnBu", "Greens", "Greys", "OrRd", "Oranges",
    "PuBu", "PuBuGn", "PuRd", "Purples", "RdPu", "Reds", "YlGn", "YlGnBu",
    "YlOrBr", "YlOrRd", "viridis", "plasma", "inferno", "magma", "cividis",
}
_DIVERGING = {
    "BrBG", "PiYG", "PRGn", "PuOr", "RdBu", "RdGy", "RdYlBu", "RdYlGn",
    "Spectral", "coolwarm", "bwr", "seismic",
}
# True qualitative matplotlib colormaps — safe to use as categorical cycles.
# (Continuous maps are stored as 256-entry ListedColormaps in modern matplotlib,
# so a `hasattr(cmap, "colors")` test wrongly treats them as qualitative.)
_QUALITATIVE = {
    "Pastel1", "Pastel2", "Paired", "Accent", "Dark2",
    "Set1", "Set2", "Set3", "tab10", "tab20", "tab20b", "tab20c",
}
_RESERVED = {"mpl", "okabe-ito", "okabe_ito"}

_custom: Dict[str, List[str]] = {}


def register_palette(name: str, colors: Sequence) -> None:
    """Register a named categorical palette from a list of colors (hex or RGB)."""
    key = name.strip().lower()
    if key in _RESERVED:
        raise ValueError(f"{name!r} is a reserved palette name.")
    try:
        hexed = [mcolors.to_hex(c) for c in colors]
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid color in palette {name!r}: {e}") from None
    if not hexed:
        raise ValueError("A palette needs at least one color.")
    _custom[key] = hexed


def cmap(name: str):
    """Return a matplotlib Colormap for ordered/heatmap data."""
    return colormaps[name]  # modern API; cm.get_cmap was removed in mpl 3.9


def palette(name: str = "okabe-ito", n: int | None = None) -> List[str]:
    """Return a list of categorical colors.

    Registered names and qualitative schemes are returned directly; sequential or
    diverging scheme names raise a warning (that's the anti-pattern) and are
    sampled as a fallback.
    """
    key = name.strip().lower()
    if key in _custom:
        cols = list(_custom[key])
    elif key in ("okabe-ito", "okabe_ito"):
        cols = list(OKABE_ITO)
    elif key == "mpl":
        cols = list(mcolors.TABLEAU_COLORS.values())
    elif key in _BUILTIN:
        cols = list(_BUILTIN[key])
    elif name in _QUALITATIVE:
        # A true qualitative colormap (Set2, Dark2, tab10…): take its discrete swatches.
        c = colormaps[name]
        k = n or getattr(c, "N", 8)
        cols = [mcolors.to_hex(c(i % c.N)) for i in range(k)]
    else:
        # Any continuous map used as a categorical cycle is the anti-pattern —
        # whether it's a known sequential/diverging name or an unlisted one
        # (turbo, jet, hsv…). Warn and sample a *small* even set, never dump c.N.
        try:
            c = colormaps[name]
        except KeyError:
            raise ValueError(
                f"Unknown palette or colormap {name!r}. "
                f"Categorical palettes: {available_palettes()}; "
                f"for ordered data use pp.cmap({name!r})."
            ) from None
        warnings.warn(
            f"{name!r} is a continuous colormap; using it as a categorical "
            f"cycle is an anti-pattern (adjacent categories look ordered/"
            f"low-contrast). Use pp.cmap({name!r}) for ordered data, or a "
            f"qualitative palette for categories.",
            stacklevel=2,
        )
        k = n or 6
        cols = [mcolors.to_hex(c(i / max(k - 1, 1))) for i in range(k)]

    if n is not None:
        cols = [cols[i % len(cols)] for i in range(n)]
    return cols


def fills(n: int | None = None) -> List[str]:
    """Muted palette for area / histogram **fills** (pairs with ``strokes()``)."""
    return palette("muted", n)


def strokes(n: int | None = None) -> List[str]:
    """Bright palette for **strokes** — lines, outlines, reference markers."""
    return palette("bright", n)


def is_colorblind_safe(name: str) -> bool:
    """Whether a named palette stays distinguishable under color-vision deficiency."""
    return name.strip().lower().replace("_", "-") in _CB_SAFE


def available_palettes() -> List[str]:
    """Names of all resolvable categorical palettes (built-in + registered)."""
    names = ["okabe-ito", *_BUILTIN, "mpl"]
    names += [k for k in _custom if k not in names]
    return names


def resolve_cycle(value) -> List[str]:
    """Coerce a palette name / color list / None into a list of cycle colors."""
    if value is None:
        return list(OKABE_ITO)
    if isinstance(value, str):
        return palette(value)
    return [mcolors.to_hex(c) for c in value]
