"""The figure maker and axes helpers.

``figure()`` (aliased ``subplots``) is the one function users touch first; it
sizes to the journal column and applies the spec's style. ``panel_labels`` /
``despine`` / ``clean_shared_axes`` are the small layout helpers.
"""

from __future__ import annotations

import string
from typing import Optional, Sequence

import importlib

import matplotlib.pyplot as plt
import numpy as np

# The public pp.style() function shadows the style submodule on the package, so
# reach the module via sys.modules rather than attribute lookup.
_style = importlib.import_module("paperplot.style")


def figure(width="single", *, aspect="golden", height=None, nrows=1, ncols=1,
           journal=None, palette=None, serif=None, math=None, font_scale=None,
           sharex=False, sharey=False,
           height_ratios: Optional[Sequence[float]] = None,
           width_ratios: Optional[Sequence[float]] = None,
           constrained: bool = True, **subplot_kw):
    """Create a journal-sized, journal-styled figure + axes.

    Returns ``(fig, ax)`` for a 1x1 grid, else ``(fig, ndarray[Axes])`` — same
    shape contract as ``plt.subplots``. ``serif``/``palette``/``math``/
    ``font_scale`` left as ``None`` inherit whatever ``pp.use()`` set.
    """
    spec = _style.resolve_spec(journal)
    _style.apply(spec, serif=serif, palette=palette, math=math,
                 font_scale=font_scale)

    figsize = spec.figsize(width, aspect=aspect, height=height)

    gridspec_kw = {}
    if height_ratios is not None:
        gridspec_kw["height_ratios"] = list(height_ratios)
    if width_ratios is not None:
        gridspec_kw["width_ratios"] = list(width_ratios)

    fig, axes = plt.subplots(
        nrows, ncols, figsize=figsize, sharex=sharex, sharey=sharey,
        layout="constrained" if constrained else None,
        gridspec_kw=gridspec_kw or None, **subplot_kw,
    )
    return fig, axes


subplots = figure  # alias


def _flatten(axes):
    if isinstance(axes, np.ndarray):
        return list(axes.ravel())
    if isinstance(axes, (list, tuple)):
        return list(axes)
    return [axes]


def _default_labels(n):
    """a, b, …, z, aa, ab, … — enough letters for ``n`` panels (>26 safe)."""
    import itertools
    out = []
    width = 1
    while len(out) < n:
        for combo in itertools.product(string.ascii_lowercase, repeat=width):
            out.append("".join(combo))
            if len(out) >= n:
                break
        width += 1
    return out


def panel_labels(axes, labels=None, *, loc="outside", offset_pt=None,
                 nudge="first-col", size=None, weight="bold", fmt="{}",
                 color="black", bbox=False, reserve=None):
    """Stamp ``a, b, c…`` panel letters on each axes.

    Args:
        loc: ``"outside"`` (above the top-left corner — the journal default) or
            ``"inside"`` (just inside the top-left of the data area).
        offset_pt: ``(dx, dy)`` nudge in points. Defaults to ``(-8, 2)`` outside
            (letters sit over the left margin) / ``(3, -3)`` inside.
        nudge: outside only — which columns shift left by ``dx``.
            ``"first-col"`` (default) shifts only the outer-left column into the
            margin, so inner columns don't widen the inter-column gap;
            ``"all"`` shifts every label; ``"none"`` ignores ``dx``.
        size: font size; defaults to the active journal's panel size.
        bbox: draw a white background box behind each letter (good for
            ``loc="inside"`` over data).
        reserve: whether labels reserve layout space. Default ``True`` for
            ``"outside"`` (so the top row never clips) and ``False`` for
            ``"inside"`` (never clips anyway — no reflow).

    ``annotation_clip`` is always off, so the axes never hide a label.
    """
    axs = _flatten(axes)
    if labels is None:
        labels = _default_labels(len(axs))   # never runs out past 26 panels
    if size is None:
        spec = _style.active()
        size = spec.font_pt.panel if spec is not None else 9.0

    inside = loc == "inside"
    if offset_pt is None:
        offset_pt = (3, -3) if inside else (-8, 2)
    dx, dy = offset_pt
    va = "top" if inside else "bottom"
    if reserve is None:
        reserve = not inside
    box = (dict(boxstyle="square,pad=0.15", fc="white", ec="none", alpha=0.85)
           if bbox else None)

    out = []
    for ax, lab in zip(axs, labels):
        ddx = dx
        if not inside and nudge != "all":
            # left-shift only escapes into the OUTER margin; inner columns sit
            # above their corner so they never widen the inter-column gap.
            ss = ax.get_subplotspec()
            if nudge == "none" or (ss is not None and ss.colspan.start != 0):
                ddx = 0
        ann = ax.annotate(
            fmt.format(lab), xy=(0, 1), xycoords="axes fraction",
            xytext=(ddx, dy), textcoords="offset points",
            ha="left", va=va, fontsize=size, fontweight=weight, color=color,
            annotation_clip=False, bbox=box)
        ann.set_in_layout(reserve)
        out.append(ann)
    return out


def despine(axes, *, top=True, right=True, left=False, bottom=False):
    """Hide the named spines (and their ticks). Inverse of the full-box default."""
    sides = {"top": top, "right": right, "left": left, "bottom": bottom}
    for ax in _flatten(axes):
        for side, drop in sides.items():
            if drop:
                ax.spines[side].set_visible(False)
        ax.tick_params(top=not top, right=not right,
                       left=not left, bottom=not bottom,
                       labeltop=False, labelright=False)


def clean_shared_axes(fig):
    """On a shared grid, keep tick labels/axis labels only on the outer edge."""
    for ax in fig.axes:
        ss = ax.get_subplotspec()
        if ss is None:
            continue
        if not ss.is_last_row():
            ax.set_xlabel("")
            ax.tick_params(labelbottom=False)
        if not ss.is_first_col():
            ax.set_ylabel("")
            ax.tick_params(labelleft=False)


def _build_grid(fig, grid_spec):
    """Builds the exact absolute coordinates for the grid."""
    # 1. Compute total figure dimensions in inches
    total_width = (grid_spec.margins["left"] + 
                   grid_spec.ncols * grid_spec.col_width + 
                   (grid_spec.ncols - 1) * grid_spec.wspace + 
                   grid_spec.margins["right"])
    
    total_height = grid_spec.margins["top"] + grid_spec.margins["bottom"]
    for r in grid_spec.rows:
        total_height += r.height + r.gap_above
        
    # Resize figure to the exact required size
    fig.set_size_inches(total_width, total_height)
    
    axes_array = np.empty((len(grid_spec.rows), grid_spec.ncols), dtype=object)
    row_names = [r.name for r in grid_spec.rows]
    
    # 2. Compute column horizontal positions (relative 0.0 to 1.0)
    lefts = []
    for c in range(grid_spec.ncols):
        x = grid_spec.margins["left"] + c * (grid_spec.col_width + grid_spec.wspace)
        lefts.append(x / total_width)
    w_frac = grid_spec.col_width / total_width
    
    # 3. Compute row vertical positions from top to bottom
    current_y = total_height - grid_spec.margins["top"]
    
    for r_idx, r in enumerate(grid_spec.rows):
        current_y -= r.gap_above
        current_y -= r.height
        
        y_frac = current_y / total_height
        h_frac = r.height / total_height
        
        for c_idx in range(grid_spec.ncols):
            # Create exact axis position
            ax = fig.add_axes([lefts[c_idx], y_frac, w_frac, h_frac])
            axes_array[r_idx, c_idx] = ax
            
            # Handle attachment semantics
            if r.attached and r_idx > 0:
                ax_above = axes_array[r_idx - 1, c_idx]
                ax.sharex(ax_above)
                ax_above.tick_params(labelbottom=False)
                ax_above.set_xlabel("")
                
    from .layout import GridAxesDict
    return GridAxesDict(axes_array, row_names)


def composite(grid=None, journal=None, palette=None, serif=None, math=None, font_scale=None):
    """Create a composite figure using the precise Grid absolute layout engine.
    
    Returns ``(fig, ax_dict)`` where ax_dict acts as both a 2D ndarray and a dictionary
    addressable by ``ax["row_name", col_index]``.
    """
    spec = _style.resolve_spec(journal)
    _style.apply(spec, serif=serif, palette=palette, math=math, font_scale=font_scale)
    
    # Create an empty figure with NO layout engine to prevent automatic squishing
    fig = plt.figure(figsize=(1, 1), layout="none")
    ax_dict = _build_grid(fig, grid)
    return fig, ax_dict
