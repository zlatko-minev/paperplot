"""``preflight()`` — validate a figure against journal rules. Warn, never block.

Returns a structured ``Report`` so CI can gate on it while humans read a table.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Union

import matplotlib.colors as mcolors

import importlib

from .journals import JournalSpec

# pp.style() shadows the style submodule on the package; reach it via sys.modules.
_style = importlib.import_module("paperplot.style")

Number = Union[float, str]


@dataclass(frozen=True)
class Finding:
    severity: str          # "warn" | "info"
    rule: str              # min_font | min_linewidth | gray_luminance
    locator: str           # human-readable artist location
    measured: Number
    limit: Number
    message: str


@dataclass(frozen=True)
class Report:
    findings: Tuple[Finding, ...]
    spec_name: str = ""

    @property
    def warnings(self) -> Tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity == "warn")

    @property
    def ok(self) -> bool:
        return not self.warnings

    def __bool__(self) -> bool:
        return self.ok

    def by_rule(self, rule: str) -> Tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.rule == rule)

    def __str__(self) -> str:
        if not self.findings:
            return f"preflight [{self.spec_name}]: OK ✓ (no issues)"
        lines = [f"preflight [{self.spec_name}]: "
                 f"{len(self.warnings)} warning(s), "
                 f"{len(self.findings) - len(self.warnings)} info"]
        for f in self.findings:
            mark = "⚠" if f.severity == "warn" else "ℹ"
            lines.append(f"  {mark} {f.message}")
        return "\n".join(lines)


def _luminance(color) -> float:
    r, g, b = mcolors.to_rgb(color)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def preflight(fig, spec: Optional[JournalSpec] = None) -> Report:
    """Inspect a drawn figure for sub-spec fonts, lines, and gray ambiguity."""
    spec = spec or _style.active()
    if spec is None:
        raise RuntimeError("No journal to check against; call pp.use('aps') or pass spec=.")

    fig.canvas.draw()  # realize tick labels / autosized artists
    fp = spec.font_pt
    # Cap-height is an info-level nag aimed at text the *user* shrank below the
    # journal's own defaults; don't fire it on the spec's chosen sizes (e.g. APS
    # 7.5pt ticks are ~1.9mm cap-height by design — reporting them is just noise).
    spec_floor_pt = min(fp.base, fp.tick, fp.legend, fp.panel)
    findings: list[Finding] = []

    for i, ax in enumerate(fig.axes):
        texts = [("title", ax.title), ("x-label", ax.xaxis.label),
                 ("y-label", ax.yaxis.label)]
        texts += [("x-tick", t) for t in ax.get_xticklabels()]
        texts += [("y-tick", t) for t in ax.get_yticklabels()]
        leg = ax.get_legend()
        if leg is not None:
            texts += [("legend", t) for t in leg.get_texts()]

        seen_kinds: set = set()
        for kind, t in texts:
            if not t.get_text():
                continue
            pt = t.get_fontsize()
            loc = f"axes[{i}] {kind}"
            if pt < fp.min_warn_pt:
                findings.append(Finding(
                    "warn", "min_font", loc, round(pt, 1), fp.min_warn_pt,
                    f"{loc}: {pt:.1f}pt < {fp.min_warn_pt}pt minimum"))
            elif (kind not in seen_kinds and pt < spec_floor_pt
                  and fp.cap_height_mm(pt) < fp.min_cap_height_mm):
                cap = fp.cap_height_mm(pt)
                findings.append(Finding(
                    "info", "min_font", loc, round(cap, 2), fp.min_cap_height_mm,
                    f"{loc}: cap-height {cap:.2f}mm < {fp.min_cap_height_mm}mm "
                    f"APS guideline (font {pt:.1f}pt)"))
            seen_kinds.add(kind)

        for j, line in enumerate(ax.get_lines()):
            lw = line.get_linewidth()
            if 0 < lw < spec.min_linewidth_pt:
                findings.append(Finding(
                    "warn", "min_linewidth", f"axes[{i}] Line2D #{j}",
                    round(lw, 2), spec.min_linewidth_pt,
                    f"axes[{i}] line #{j}: {lw:.2f}pt < "
                    f"{spec.min_linewidth_pt}pt minimum weight"))

        # collection-based artists (LineCollection from step/quiver/etc.) carry
        # their own linewidths and would otherwise dodge the Line2D check.
        for j, coll in enumerate(ax.collections):
            try:
                lws = [float(w) for w in coll.get_linewidths()]
            except (TypeError, ValueError):
                continue
            thin = [w for w in lws if 0 < w < spec.min_linewidth_pt]
            if thin:
                w = min(thin)
                findings.append(Finding(
                    "warn", "min_linewidth", f"axes[{i}] collection #{j}",
                    round(w, 2), spec.min_linewidth_pt,
                    f"axes[{i}] collection #{j}: {w:.2f}pt < "
                    f"{spec.min_linewidth_pt}pt minimum weight"))

    # cycle-color grayscale separability (print is grayscale, APS H24)
    try:
        import matplotlib as mpl
        from . import palettes
        colors = mpl.rcParams["axes.prop_cycle"].by_key().get("color", [])
        # Don't nag about the shipped default: Okabe-Ito is curated colorblind-safe,
        # and its grayscale gaps are a known, accepted trade-off.
        cur = [mcolors.to_hex(c).lower() for c in colors]
        default = [mcolors.to_hex(c).lower() for c in palettes.OKABE_ITO]
        is_default = bool(cur) and cur == default[:len(cur)]
        lums = sorted(_luminance(c) for c in colors[:6])
        gaps = [b - a for a, b in zip(lums, lums[1:])]
        if not is_default and gaps and min(gaps) < 0.05:
            findings.append(Finding(
                "info", "gray_luminance", "color cycle", round(min(gaps), 3), 0.05,
                "two cycle colors are near-identical in grayscale; check the "
                "figure stays legible in print (APS H24)"))
    except Exception:
        pass

    return Report(tuple(findings), spec_name=spec.name)
