"""Notebook preview helpers for small publication figures.

- ``show(fig, zoom)``  : magnify the real figure (SVG) without mutating it.
- ``preview_in_page``  : embed the figure at true scale in a mock journal page.
- ``grayscale_proof``  : render desaturated to check APS print legibility.
"""

from __future__ import annotations

import importlib
import io

import matplotlib.pyplot as plt

from . import layout

# pp.style() shadows the style submodule on the package; reach it via sys.modules.
_style = importlib.import_module("paperplot.style")

# Bundled placeholder text (no external 'lorem' dependency).
LOREM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod "
    "tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, "
    "quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo "
    "consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse "
    "cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non "
    "proident, sunt in culpa qui officia deserunt mollit anim id est laborum. "
)


def _svg_bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="svg")  # no bbox_inches='tight' -> stable geometry
    return buf.getvalue()


def show(fig, zoom: float = 2.0):
    """Display ``fig`` magnified by ``zoom`` in a notebook. Figure untouched.

    Renders to SVG (vector, crisp at any zoom) and scales the <svg> width/height.
    Returns the IPython SVG object (also auto-displays in a notebook).
    """
    try:
        from IPython.display import SVG, display
    except ImportError as e:  # optional extra: paperplot[notebook]
        raise ImportError(
            "show() needs IPython. Install paperplot[notebook] or use "
            "preview_in_page() (pure matplotlib)."
        ) from e

    svg = _svg_bytes(fig).decode("utf-8")
    w_in, h_in = fig.get_size_inches()
    style_attr = f'style="width:{w_in * zoom:.3f}in;height:{h_in * zoom:.3f}in;"'
    # inject a sizing style on the first <svg ...> tag
    svg = svg.replace("<svg ", f"<svg {style_attr} ", 1)
    obj = SVG(data=svg)
    display(obj)
    return obj


def _justify_column(bg, x0, y_top, col_w, chunk, pt, family, color,
                    linespacing, renderer, cache):
    """Render a column of text fully justified (last line left-aligned)."""
    line_h = pt / 72.0 * linespacing
    y = y_top
    n = len(chunk)
    for i, line in enumerate(chunk):
        words = line.split()
        is_last = i == n - 1
        if len(words) > 1 and not is_last:
            widths = []
            for w in words:
                if w not in cache:
                    tmp = bg.text(0, -1000, w, fontsize=pt, family=family)
                    cache[w] = tmp.get_window_extent(renderer).width / renderer.dpi
                    tmp.remove()
                widths.append(cache[w])
            gap = (col_w - sum(widths)) / (len(words) - 1)
            if 0 <= gap <= col_w:  # sane spacing only
                x = x0
                for w, ww in zip(words, widths):
                    bg.text(x, y, w, fontsize=pt, family=family, color=color,
                            va="top", ha="left")
                    x += ww + gap
                y -= line_h
                continue
        bg.text(x0, y, line, fontsize=pt, family=family, color=color,
                va="top", ha="left")  # ragged fallback / last line
        y -= line_h


def preview_in_page(fig, width="single", *, journal=None, page=(8.5, 11.0),
                    columns: int = 2, dpi: int = 150, text=None,
                    body_pt=None, show_info: bool = True, justify: bool = True,
                    figure_box: bool = False):
    """Embed ``fig`` at true physical scale inside a mock journal page.

    The surrounding text is real placeholder prose (lorem ipsum by default,
    override via ``text``) rendered in serif at the journal's body font size
    (``spec.page_body_pt``), so the figure-to-text scale is faithful. A header
    lists the journal, column, physical width, and the body/figure font sizes.

    Args:
        justify: fully justify the body text (default True) so column edges line
            up with the figure; set False for ragged-right.
        figure_box: draw the figure's bounding box (default False) — useful to
            confirm the figure width equals the column width.

    Returns a NEW matplotlib Figure (the proof). True scale holds when the proof
    is viewed/printed at 100%.
    """
    import textwrap
    import matplotlib.image as mpimg
    import matplotlib.patches as mpatches

    spec = _style.resolve_spec(journal)
    wkey = layout.resolve_width(width)
    w_lookup = "double" if wkey == "full_page" else wkey
    body_pt = float(body_pt if body_pt is not None else spec.page_body_pt)
    page_w, page_h = page
    fig_w_in, fig_h_in = fig.get_size_inches()

    # Make the mock page geometrically faithful: page columns == journal columns.
    col_w = layout.mm_to_in(spec.widths_mm["single"])
    double_w = layout.mm_to_in(spec.widths_mm.get("double", 2 * spec.widths_mm["single"]))
    gutter = max(0.12, double_w - 2 * col_w) if columns == 2 else 0.2
    block_w = columns * col_w + (columns - 1) * gutter
    margin_x = max(0.4, (page_w - block_w) / 2)
    margin_y = 0.8

    proof = plt.figure(figsize=(page_w, page_h), dpi=dpi)
    proof.patch.set_facecolor("white")
    bg = proof.add_axes([0, 0, 1, 1])
    bg.set_xlim(0, page_w)
    bg.set_ylim(0, page_h)
    bg.axis("off")
    top = page_h - margin_y

    # --- info header: list exactly what this is ---
    if show_info:
        w_in = layout.mm_to_in(spec.widths_mm[w_lookup])
        info = (f"{spec.name}   ·   {wkey} column   ·   "
                f"{spec.widths_mm[w_lookup]:.0f} mm ({w_in:.2f} in) wide   ·   "
                f"body {body_pt:g} pt   ·   figure text {spec.font_pt.base:g} pt")
        bg.text(margin_x, page_h - 0.45, info, fontsize=7, family="sans-serif",
                color="0.45", va="bottom", ha="left")
        bg.plot([margin_x, margin_x + block_w], [page_h - 0.52] * 2,
                color="0.8", lw=0.6)

    # --- embed the real figure at true inches (top of column 0) ---
    spans = fig_w_in > col_w * 1.5
    fig_bottom = top - fig_h_in
    ax_fig = proof.add_axes([margin_x / page_w, fig_bottom / page_h,
                             fig_w_in / page_w, fig_h_in / page_h])
    png = io.BytesIO()
    fig.savefig(png, format="png", dpi=300, facecolor="white")
    png.seek(0)
    ax_fig.imshow(mpimg.imread(png))
    ax_fig.axis("off")
    if figure_box:
        bg.add_patch(mpatches.Rectangle(
            (margin_x, fig_bottom), fig_w_in, fig_h_in,
            fill=False, edgecolor="0.55", lw=0.8))

    # --- figure caption (serif, italic, at figure text size) ---
    cap_pt = spec.font_pt.base
    cap_y = fig_bottom - 0.07
    bg.text(margin_x, cap_y,
            f"FIG. 1. Placeholder figure shown at true {wkey}-column scale.",
            fontsize=cap_pt, family="serif", style="italic",
            va="top", ha="left", color="0.2")
    after_caption = cap_y - cap_pt / 72.0 * 1.7 - 0.08

    # --- body text: real lorem ipsum at the journal body size, flowing columns ---
    body = text if text is not None else (LOREM * 14)
    chars = max(12, int(col_w * 72.0 / (0.46 * body_pt)))
    lines = textwrap.wrap(body, width=chars)
    linespacing = 1.45
    line_h = body_pt / 72.0 * linespacing

    # a renderer is needed to measure word widths for justification
    proof.canvas.draw()
    renderer = proof.canvas.get_renderer()
    cache: dict = {}

    idx = 0
    for c in range(columns):
        x0 = margin_x + c * (col_w + gutter)
        if spans:
            col_top = after_caption
        else:
            col_top = after_caption if c == 0 else top
        nfit = max(0, int((col_top - margin_y) / line_h))
        chunk = lines[idx:idx + nfit]
        idx += nfit
        if not chunk:
            continue
        if justify:
            _justify_column(bg, x0, col_top, col_w, chunk, body_pt, "serif",
                            "0.15", linespacing, renderer, cache)
        else:
            bg.text(x0, col_top, "\n".join(chunk), fontsize=body_pt,
                    family="serif", color="0.15", va="top", ha="left",
                    linespacing=linespacing)
    return proof


def grayscale_proof(fig, dpi: int = 200):
    """Return a NEW figure showing ``fig`` desaturated (APS print reality)."""
    import numpy as np
    import matplotlib.image as mpimg

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor="white")
    buf.seek(0)
    rgb = mpimg.imread(buf)[..., :3]
    gray = rgb @ np.array([0.2126, 0.7152, 0.0722])

    w_in, h_in = fig.get_size_inches()
    proof = plt.figure(figsize=(w_in, h_in), dpi=dpi)
    ax = proof.add_axes([0, 0, 1, 1])
    ax.imshow(gray, cmap="gray", vmin=0, vmax=1)
    ax.axis("off")
    return proof
