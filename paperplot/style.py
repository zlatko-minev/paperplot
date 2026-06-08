"""rcParams construction and the use/style/reset lifecycle.

``rcparams(spec, ...)`` is the core translation layer (spec -> matplotlib rc).
``use()`` sets a sticky global journal; ``style()`` is a scoped context manager
(full save/restore); ``reset()`` undoes ``use()``.
"""

from __future__ import annotations

import contextlib
import copy
from typing import Optional

import matplotlib as mpl
from cycler import cycler

from . import fonts, palettes
from .journals import JournalSpec
from .registry import get_spec

_active: Optional[JournalSpec] = None
_snapshot: Optional[dict] = None

# The styling options last set by use(); figure()/style() inherit these unless a
# call overrides them (pass the kwarg). reset() restores the defaults.
_DEFAULT_OPTS = {"serif": False, "palette": None, "usetex": False,
                 "math": "cm", "font_scale": 1.0}
_active_opts: dict = dict(_DEFAULT_OPTS)

# math= names -> matplotlib mathtext.fontset. Default "cm" gives the Computer
# Modern look physics figures expect, even with sans-serif text labels.
_MATH_FONTSET = {
    "cm": "cm",            # Computer Modern (LaTeX look) — default
    "stix": "stix",        # Times-like math, pairs with serif=True
    "stixsans": "stixsans",
    "sans": "stixsans",    # clean sans math that pairs with Arial/Helvetica
    "dejavusans": "dejavusans",
}


def _mathset(math: str, serif: bool) -> str:
    if math == "auto":
        return "cm" if serif else "stixsans"
    return _MATH_FONTSET.get(math, math)


def _effective(serif=None, palette=None, usetex=None, math=None,
               font_scale=None) -> dict:
    """Fill any unspecified (None) option from the active use() options."""
    o = _active_opts
    return {
        "serif": o["serif"] if serif is None else serif,
        "palette": o["palette"] if palette is None else palette,
        "usetex": o["usetex"] if usetex is None else usetex,
        "math": o["math"] if math is None else math,
        "font_scale": o["font_scale"] if font_scale is None else font_scale,
    }


def resolve_spec(journal) -> JournalSpec:
    """Resolve a journal arg (str / JournalSpec / None) to a spec."""
    if isinstance(journal, JournalSpec):
        return journal
    if journal is not None:
        return get_spec(journal)
    if _active is not None:
        return _active
    raise RuntimeError(
        "No active journal. Call pp.use('aps') first, or pass journal=..."
    )


def rcparams(spec: JournalSpec, *, serif: bool = False, usetex: bool = False,
             palette=None, math: str = "cm", font_scale: float = 1.0) -> dict:
    """Build the matplotlib rcParams dict for a spec.

    ``math`` selects the mathtext font set (``"cm"``/``"sans"``/``"stix"``/
    ``"auto"``); ``font_scale`` multiplies every spec point size (a deliberate
    nudge — preflight still warns below the journal's absolute minimum).
    """
    fonts.register_bundled()
    fp = spec.font_pt
    s = float(font_scale)
    lw = spec.min_linewidth_pt
    cycle_colors = palettes.resolve_cycle(palette)
    return {
        # fonts
        "font.family": "serif" if serif else "sans-serif",
        "font.sans-serif": list(spec.font_family),
        "font.serif": ["Times", "Nimbus Roman", "DejaVu Serif"],
        "font.size": fp.base * s,
        "axes.labelsize": fp.base * s,
        "axes.titlesize": fp.base * s,
        "xtick.labelsize": fp.tick * s,
        "ytick.labelsize": fp.tick * s,
        "legend.fontsize": fp.legend * s,
        "legend.title_fontsize": fp.base * s,
        "figure.titlesize": fp.base * s,
        "mathtext.fontset": _mathset(math, serif),
        "text.usetex": usetex,
        "axes.unicode_minus": not usetex,
        "axes.formatter.use_mathtext": True,
        # lines / ticks / spines (>= min line weight). Plot lines scale with the
        # journal's min weight so talk targets get thicker strokes for projection
        # while APS/Nature (min 0.5) keep the 1.0 pt publication default.
        "axes.linewidth": max(0.6, lw),
        "lines.linewidth": max(1.0, 2.0 * lw),
        "lines.markersize": max(3.0, 3.0 * lw / 0.5),
        "lines.markeredgewidth": 0.5,
        "patch.linewidth": 0.6,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.major.width": lw,
        "ytick.major.width": lw,
        "xtick.minor.width": 0.4,
        "ytick.minor.width": 0.4,
        "xtick.major.size": 3.0,
        "ytick.major.size": 3.0,
        "xtick.minor.size": 1.5,
        "ytick.minor.size": 1.5,
        "xtick.major.pad": 3,
        "ytick.major.pad": 3,
        "axes.titlepad": 3,
        "axes.labelpad": 2,
        "axes.xmargin": 0.02,
        "axes.ymargin": 0.02,
        # full box (APS); pp.despine() removes top/right on demand
        "axes.spines.top": True,
        "axes.spines.right": True,
        # color cycle
        "axes.prop_cycle": cycler(color=cycle_colors),
        # figure / save
        "figure.figsize": list(spec.figsize("single")),
        "figure.facecolor": "white",
        "figure.dpi": 150,
        "savefig.dpi": spec.rasterize_dpi.get("line", 600),
        "savefig.bbox": "standard",
        "savefig.pad_inches": 0.01,
        "savefig.transparent": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }


def apply(spec: JournalSpec, *, serif=None, palette=None, usetex=None,
          math=None, font_scale=None) -> None:
    """Update the global rcParams in place (used by use() and figure()).

    Unspecified (None) options fall back to whatever ``use()`` last set, so
    per-figure calls inherit the active style instead of resetting it.
    """
    eff = _effective(serif, palette, usetex, math, font_scale)
    mpl.rcParams.update(rcparams(spec, **eff))


def use(journal, *, serif: bool = False, palette=None, usetex: bool = False,
        math: str = "cm", font_scale: float = 1.0) -> JournalSpec:
    """Set the sticky active journal + style options and apply them globally."""
    global _active, _snapshot, _active_opts
    spec = resolve_spec(journal)
    if _snapshot is None:  # remember the pre-paperplot state for reset()
        _snapshot = copy.deepcopy(dict(mpl.rcParams))
    _active_opts = {"serif": serif, "palette": palette, "usetex": usetex,
                    "math": math, "font_scale": font_scale}
    apply(spec)  # uses the just-stored active options
    _active = spec
    return spec


def active() -> Optional[JournalSpec]:
    return _active


def reset() -> None:
    """Restore rcParams to the state before the first use(), and clear active."""
    global _active, _snapshot, _active_opts
    if _snapshot is not None:
        mpl.rcParams.update(_snapshot)
        _snapshot = None
    _active = None
    _active_opts = dict(_DEFAULT_OPTS)


@contextlib.contextmanager
def style(journal=None, *, serif=None, palette=None, usetex=None,
          math=None, font_scale=None):
    """Scoped styling: applies a spec's rcParams, restores fully on exit.

    Unspecified options inherit the active ``use()`` style (or the defaults).
    """
    spec = resolve_spec(journal)
    eff = _effective(serif, palette, usetex, math, font_scale)
    with mpl.rc_context(rcparams(spec, **eff)):
        yield spec
