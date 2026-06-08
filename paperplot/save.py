"""Saving figures with publication-correct defaults.

PDF default, EPS first-class. Fonts embedded (Type-42, no Type-3) for pdf+ps.
Runs preflight() and surfaces warnings. Warns on alpha in EPS (matplotlib
rasterizes it) and stamps the spec revision into PDF metadata.
"""

from __future__ import annotations

import importlib
import warnings
from pathlib import Path

import matplotlib as mpl

# pp.style() shadows the style submodule on the package; reach it via sys.modules.
_style = importlib.import_module("paperplot.style")
from .lint import preflight as _preflight

_VECTOR = {"pdf", "eps", "svg", "ps"}


def _color_has_alpha(artist) -> bool:
    """True if any face/edge color on the artist is RGBA with alpha < 1."""
    for getter in ("get_facecolor", "get_edgecolor"):
        fn = getattr(artist, getter, None)
        if fn is None:
            continue
        try:
            col = fn()
        except Exception:
            continue
        import numpy as np
        arr = np.atleast_2d(np.asarray(col, dtype=float))
        if arr.ndim == 2 and arr.shape[1] == 4 and (arr[:, 3] < 1.0).any():
            return True
    return False


def _has_alpha(fig) -> bool:
    # Scan figure-level artists + every axes child for transparency, via the
    # alpha attribute *and* RGBA face/edge colors (fill_between, scatter, etc.).
    artists = [fig.patch, *getattr(fig, "legends", [])]
    for ax in fig.axes:
        artists.extend(ax.get_children())
    for artist in artists:
        a = getattr(artist, "get_alpha", lambda: None)()
        if a is not None and a < 1.0:
            return True
        if _color_has_alpha(artist):
            return True
    return False


def save(fig, path, *, dpi=None, run_preflight=True, journal=None, **savefig_kw):
    """Save ``fig`` to ``path`` with journal-correct export settings.

    Format is taken from the extension; no extension defaults to ``.pdf``.
    Returns the preflight :class:`~paperplot.lint.Report` (or None if skipped).
    """
    spec = _style.resolve_spec(journal)
    p = Path(path)
    fmt = p.suffix.lower().lstrip(".")
    if not fmt:
        p = p.with_suffix(".pdf")
        fmt = "pdf"

    if fmt in ("eps", "ps") and _has_alpha(fig):
        warnings.warn(
            f"{fmt.upper()} target: figure has alpha<1 artists; matplotlib "
            f"rasterizes transparency in {fmt.upper()}. Use PDF to keep them vector.",
            stacklevel=2,
        )

    report = None
    if run_preflight:
        report = _preflight(fig, spec)
        for f in report.warnings:
            warnings.warn(f"preflight: {f.message}", stacklevel=2)

    if dpi is None and fmt not in _VECTOR:
        dpi = spec.rasterize_dpi.get("line", 600)

    metadata = None
    if fmt == "pdf":
        metadata = {"Creator": f"paperplot ({spec.name} {spec.revision})"}

    kw = dict(facecolor="white")
    if dpi is not None:
        kw["dpi"] = dpi
    if metadata is not None:
        kw["metadata"] = metadata
    kw.update(savefig_kw)

    # Embed fonts as Type-42 (never Type-3) scoped to this save — don't mutate
    # the caller's global rcParams.
    with mpl.rc_context({"pdf.fonttype": 42, "ps.fonttype": 42}):
        fig.savefig(p, **kw)
    return report
