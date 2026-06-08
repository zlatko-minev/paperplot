"""paperplot — publication-correct matplotlib figures, journal by journal.

Quickstart::

    import paperplot as pp

    pp.use("aps")                       # set the journal once
    fig, ax = pp.figure(width="single") # journal-sized, journal-styled
    ax.plot(x, y)
    pp.save(fig, "fig1.pdf")            # embeds fonts, runs preflight()

Ships Physical Review (APS, incl. PRL/PRX/PRB), Nature, and IEEE, plus a "talk"
presentation target. matplotlib-only core; seaborn/IPython optional.
"""

from __future__ import annotations

from .journals import FontScale, JournalSpec
from .layout import Width, Row, Grid
from .lint import Finding, Report, preflight
from .palettes import (
    OKABE_ITO,
    available_palettes,
    cmap,
    fills,
    is_colorblind_safe,
    palette,
    register_palette,
    strokes,
)
from .preview import grayscale_proof, preview_in_page, show
from .registry import available, get_spec
from .style import active, apply, rcparams, reset, style, use
from .core import (
    clean_shared_axes,
    despine,
    figure,
    panel_labels,
    subplots,
    composite,
)
from .plots import (
    data_fit_band,
    hist_filled,
    hist_outline,
    show_palettes,
    swatches,
)
from .save import save
from .mplstyle import export_mplstyle, register_mplstyles, to_mplstyle_text

__version__ = "0.1.0"

__all__ = [
    # types
    "JournalSpec", "FontScale", "Width", "Report", "Finding",
    "Row", "Grid",
    # journal / style
    "use", "style", "reset", "active", "apply", "rcparams",
    "get_spec", "available",
    # figures
    "figure", "subplots", "composite", "save",
    # helpers
    "panel_labels", "despine", "clean_shared_axes",
    # colors
    "palette", "cmap", "register_palette", "OKABE_ITO", "fills", "strokes",
    "available_palettes", "is_colorblind_safe",
    # plot helpers
    "hist_outline", "hist_filled", "data_fit_band", "swatches", "show_palettes",
    # preview
    "show", "preview_in_page", "grayscale_proof",
    # mplstyle on-ramp
    "export_mplstyle", "to_mplstyle_text", "register_mplstyles",
    # lint
    "preflight",
    "__version__",
]
