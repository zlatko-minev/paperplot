"""Opinionated publication plot helpers — the few composites that come up over and
over in physics figures and that bare matplotlib makes fiddly:

* :func:`hist_outline` — a translucent filled histogram with a crisp staircase
  outline drawn on top. The outline is what keeps *overlapping* histograms
  legible; ``ax.hist`` alone muddies them.
* :func:`hist_filled` — the lighter, centers-based shaded histogram
  (``fill_between(step="mid")`` + ``steps-mid`` line), with optional peak rescale.
* :func:`data_fit_band` — the "data points (error bars, black-edged markers) +
  bold fit line + shaded confidence band" composite used for ZNE / decay fits.
* :func:`swatches` — render color swatches to eyeball a palette (the inline
  ``display(sns.color_palette(...))`` experience, but in matplotlib).

matplotlib-only by default; :func:`hist_outline` has an opt-in ``use_seaborn``
path that draws the fill via ``seaborn.histplot`` (KDE, multiple stats, etc.).
The default colors follow paperplot's fill/stroke convention: muted fills under
bright/black strokes (see :func:`paperplot.fills` / :func:`paperplot.strokes`).
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from . import palettes


def _ensure_ax(ax):
    if ax is None:
        import matplotlib.pyplot as plt
        _, ax = plt.subplots()
    return ax


def _staircase(counts, edges):
    """Bin counts/edges -> (x, y) tracing the histogram outline as a staircase."""
    x = np.repeat(edges, 2)[1:-1]
    y = np.repeat(counts, 2)
    return x, y


def hist_outline(
    data,
    ax=None,
    *,
    bins=50,
    range=None,
    density=False,
    rescale=False,
    color=None,
    alpha=0.6,
    fill=True,
    label=None,
    outline_color="k",
    outline_lw=1.0,
    outline_kw: Optional[dict] = None,
    zorder=None,
    use_seaborn=False,
    **fill_kw,
):
    """Filled histogram with a solid staircase outline traced over the bars.

    Returns ``(ax, (counts, edges))``. The fill carries the legend ``label``.

    Parameters
    ----------
    data : array-like
        Samples to histogram.
    bins, range, density :
        Passed to ``numpy.histogram`` (and to ``seaborn.histplot`` when
        ``use_seaborn=True``). ``density`` controls the y-scale.
    rescale : bool
        Normalize counts so the tallest bin is 1 (a "relative probability"
        y-axis). Ignored when ``density=True``.
    color : color, optional
        Fill color. Defaults to the first muted fill color (``pp.fills()[0]``).
    outline_color, outline_lw, outline_kw :
        The staircase outline. ``outline_kw`` overrides any of these per call.
    use_seaborn : bool
        Draw the fill via ``seaborn.histplot`` (enables KDE, stat=, etc. through
        ``**fill_kw``) instead of ``ax.fill_between``. The outline is always
        matplotlib. Raises ``ImportError`` if seaborn is not installed.
    """
    ax = _ensure_ax(ax)
    if color is None:
        color = palettes.fills()[0]
    z = {} if zorder is None else {"zorder": zorder}

    counts, edges = np.histogram(data, bins=bins, range=range, density=density)
    counts = counts.astype(float)
    if rescale and not density and counts.max() > 0:
        counts = counts / counts.max()

    if use_seaborn:
        import seaborn as sns  # optional extra; only imported on request
        sns.histplot(
            data, ax=ax, bins=bins, binrange=range,
            stat="density" if density else "count",
            color=color, alpha=alpha, label=label, **z, **fill_kw,
        )
    elif fill:
        x, y = _staircase(counts, edges)
        ax.fill_between(x, y, color=color, alpha=alpha, linewidth=0,
                        label=label, **z, **fill_kw)

    x, y = _staircase(counts, edges)
    okw = {"color": outline_color, "linestyle": "-", "linewidth": outline_lw}
    okw.update(z)
    if outline_kw:
        okw.update(outline_kw)
    # If there is no fill to carry the label (fill=False, no seaborn), let the
    # outline carry it instead.
    if label is not None and not fill and not use_seaborn:
        okw.setdefault("label", label)
    ax.plot(x, y, **okw)

    return ax, (counts, edges)


def hist_filled(
    data,
    ax=None,
    *,
    bins=50,
    range=None,
    density=False,
    rescale=False,
    color=None,
    alpha=0.7,
    label=None,
    line_color="k",
    line_lw=1.0,
    line_kw: Optional[dict] = None,
    fill_kw: Optional[dict] = None,
    zorder=None,
):
    """Shaded histogram drawn on bin *centers* (``steps-mid``), with a line on top.

    Lighter sibling of :func:`hist_outline` — the shape is centered on bins rather
    than tracing the bar edges. Returns ``(counts, edges, centers)``.
    """
    ax = _ensure_ax(ax)
    if color is None:
        color = palettes.fills()[0]
    z = {} if zorder is None else {"zorder": zorder}

    counts, edges = np.histogram(data, bins=bins, range=range, density=density)
    counts = counts.astype(float)
    if rescale and not density and counts.max() > 0:
        counts = counts / counts.max()
    centers = (edges[:-1] + edges[1:]) / 2

    fkw = {"step": "mid", "alpha": alpha, "color": color, "linewidth": 0,
           "label": label}
    fkw.update(z)
    if fill_kw:
        fkw.update(fill_kw)
    ax.fill_between(centers, counts, **fkw)

    lkw = {"drawstyle": "steps-mid", "color": line_color, "linewidth": line_lw}
    lkw.update(z)
    if line_kw:
        lkw.update(line_kw)
    ax.plot(centers, counts, **lkw)

    return counts, edges, centers


def data_fit_band(
    ax,
    x,
    y,
    *,
    yerr=None,
    x_fit=None,
    y_fit=None,
    y_fit_err=None,
    color=None,
    fit_color=None,
    band_color=None,
    label=None,
    fit_label=None,
    band_alpha=0.2,
    data_kw: Optional[dict] = None,
    fit_kw: Optional[dict] = None,
    band_kw: Optional[dict] = None,
):
    """Plot measured data with error bars, an overlaid fit line, and a CI band.

    The standard decay-fit composite:

    * data as black-edged markers with error bars (``capsize``, thin ``mew``),
    * a bold fit line drawn *behind* the markers (``zorder=0``),
    * a translucent confidence band from ``y_fit ± y_fit_err`` (``zorder=-1``).

    Pass ``x_fit``/``y_fit`` (e.g. from ``lmfit`` ``result.eval``) to draw the
    fit, and ``y_fit_err`` (e.g. ``result.eval_uncertainty``) to add the band.
    ``color`` is the data color; ``fit_color`` and ``band_color`` default to it.
    """
    if color is None:
        color = palettes.strokes()[0]
    if fit_color is None:
        fit_color = color
    if band_color is None:
        band_color = fit_color

    dkw = {"fmt": "o", "ms": 3, "mec": "k", "mew": 0.25, "lw": 0.5,
           "capsize": 3, "color": color, "label": label}
    if data_kw:
        dkw.update(data_kw)
    ax.errorbar(x, y, yerr=yerr, **dkw)

    if x_fit is not None and y_fit is not None:
        fkw = {"lw": 2.0, "zorder": 0, "color": fit_color, "label": fit_label}
        if fit_kw:
            fkw.update(fit_kw)
        ax.plot(x_fit, y_fit, **fkw)

        if y_fit_err is not None:
            bkw = {"alpha": band_alpha, "color": band_color, "zorder": -1,
                   "linewidth": 0}
            if band_kw:
                bkw.update(band_kw)
            y_fit = np.asarray(y_fit)
            y_fit_err = np.asarray(y_fit_err)
            ax.fill_between(x_fit, y_fit - y_fit_err, y_fit + y_fit_err, **bkw)

    return ax


def _draw_swatch_rows(ax, rows, *, tags=None, tag_color="#1a7f4b"):
    """Draw labeled swatch rows on ``ax``. ``rows`` is a list of (name, colors);
    ``tags`` is an optional list of short right-side annotations (one per row)."""
    import matplotlib.pyplot as plt

    nrows = len(rows)
    ncols = max((len(c) for _, c in rows), default=0)
    for r, (name, cols) in enumerate(rows):
        yr = nrows - 1 - r
        for i, c in enumerate(cols):
            ax.add_patch(plt.Rectangle((i, yr + 0.04), 0.92, 0.92, color=c))
        if name:
            ax.text(-0.25, yr + 0.5, str(name), ha="right", va="center")
        if tags and tags[r]:
            ax.text(ncols + 0.25, yr + 0.5, tags[r], ha="left", va="center",
                    color=tag_color, weight="bold")
    ax.set_xlim(0, ncols)
    ax.set_ylim(0, nrows)
    ax.axis("off")
    return ncols, nrows


def swatches(colors, ax=None, *, labels=None, size=0.6):
    """Render color swatches — eyeball a palette or compare fills vs strokes.

    ``colors`` is a list of colors (one row) or a ``{name: [colors]}`` dict (one
    row per name). Returns the ``Figure``. The matplotlib analogue of
    ``display(sns.color_palette(...))`` in a notebook.
    """
    import matplotlib.pyplot as plt

    if isinstance(colors, dict):
        rows = list(colors.items())
    else:
        rows = [(labels if isinstance(labels, str) else "", list(colors))]

    ncols = max((len(c) for _, c in rows), default=0)
    if ax is None:
        fig, ax = plt.subplots(figsize=(1.6 + size * ncols, 0.3 + size * len(rows)))
    else:
        fig = ax.figure
    _draw_swatch_rows(ax, rows)
    ax.set_aspect("equal")
    return fig


def show_palettes(names=None, *, n=10, size=0.42):
    """First-class palette reference: swatches for every available palette, each
    tagged with whether it is colorblind-safe, plus a one-line summary footnote.

    ``names`` defaults to :func:`paperplot.available_palettes` (built-in +
    anything you registered). Returns the ``Figure``.
    """
    import matplotlib.pyplot as plt
    from . import palettes

    if names is None:
        names = palettes.available_palettes()

    rows, tags = [], []
    for nm in names:
        rows.append((nm, palettes.palette(nm, n)))
        tags.append("colorblind-safe" if palettes.is_colorblind_safe(nm) else "")

    nrows = len(rows)
    fig_w = 3.8 + size * n          # label gutter + swatches + tag gutter
    fig_h = 0.7 + size * nrows
    fig = plt.figure(figsize=(fig_w, fig_h))
    # Fixed-inch gutters so labels/tags never clip; swatch block fills the middle.
    left = 1.4 / fig_w
    ax = fig.add_axes([left, 0.55 / fig_h,
                       (size * n) / fig_w, (size * nrows) / fig_h])
    _draw_swatch_rows(ax, rows, tags=tags)

    fig.text(0.5, 0.12 / fig_h,
             "Green tag = stays distinguishable under color-vision deficiency.   "
             "muted = fills | bright = strokes (pair them; not for categorical lines).",
             ha="center", va="bottom", fontsize=7, color="0.35")
    return fig
