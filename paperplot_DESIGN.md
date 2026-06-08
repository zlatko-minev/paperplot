# paperplot — Design Document

A clean, standalone, lightweight-but-extensible Matplotlib styling package for
publication figures.  

> Status: **implemented.** This records the design decisions and trade-offs
> behind the shipped package. Resolved decisions are marked ✅.

---

## 0. Resolved decisions (were open questions)

- ✅ **Sticky journal, scoped styling.** `pp.use("aps")` sets the active journal +
  applies a scoped style; `pp.figure(...)`/`pp.save(...)` then need no journal arg.
  Explicit `journal=` is an optional per-call override. `style()` is a context
  manager (full rcParams save/restore via `mpl.rc_context`); `reset()` restores.
- ✅ **Default sans, with `serif=True`** to match REVTeX Times — and mathtext
  font set is tied to the text choice (sans→dejavusans/stixsans, serif→cm),
  plus an opt-in `usetex=True` path for body-identical figure math.
- ✅ **One `aps` spec + optional variants** (`prl`, `prx`, `prb`…) expressed as
  small overrides. Users never need to learn variants to start.
- ✅ **matplotlib-only core.** seaborn and IPython are optional extras
  (`paperplot[seaborn]`, `paperplot[notebook]`), lazy-imported behind guards.
- ✅ **Python ≥ 3.10.** `tomllib` on 3.11+, `tomli` backport on 3.10
  (`tomli; python_version < "3.11"`).
- ✅ **PDF is the default save format; EPS is first-class.** `pp.save(fig, "f")`
  with no extension → PDF (handles transparency). Extension overrides
  (`f.eps` → EPS). EPS path warns on alpha artists (§9).
- ✅ **Lint policy: warn, never block.** `preflight()` and `save()` always
  produce the file and surface warnings; no strict/raising mode in v1. Authors
  stay in control; CI gating can inspect the returned `Report` themselves.

---

## 1. Goals & non-goals

**Goals**
- One-line, journal-correct figures from the top; extensible underneath.
- Specs are **data, not docstrings** — queryable, testable, versioned, auditable.
- **matplotlib-only core**, pip-installable standalone, fast/silent first import.
- **Pre-submission linting** (`preflight`) against journal rules — the differentiator.
- Non-global by default (context managers); opt-in sticky global for notebooks.

**Non-goals (v1)**
- Not a general analysis/plotting library — no dataframe plotters, faceting/grid
  engines, 3D helpers, or domain (physics) utilities. Styling, sizing, and
  preflight remain the core.
  - ⚠️ **Scope amendment:** a *small, opinionated* set of composite plot
    helpers now ships in `plots.py` — `hist_outline`/`hist_filled` (filled
    histograms with outlines), `data_fit_band` (markers + fit + CI band), and
    `swatches`. These are the few publication composites bare matplotlib makes
    fiddly; they are thin, matplotlib-only (seaborn is an opt-in path in
    `hist_outline`), and don't pull in dataframes or a grammar-of-graphics. The
    line we still hold: no general plotting engine, no dataframe/faceting layer.
- Multi-journal via data: new journals are pure `journals.toml` additions, no
  code (this validates the registry-as-data bet). Ships **Physical Review (APS)**,
  **Nature**, and **IEEE**, plus a non-journal **`talk`** presentation *target*
  (larger type, thicker lines). To make `talk` work without special-casing,
  `lines.linewidth`/`markersize` derive from the target's `min_linewidth_pt`
  (APS/Nature/IEEE at 0.5 keep the 1.0 pt default; `talk` at 1.0 gets 2.0 pt).
  - ✅ **`.mplstyle` on-ramp (`mplstyle.py`).** Style sheets are how much of the
    matplotlib community already adopts a look (`plt.style.use(...)`, no API), so
    we expose ours the same way: `export_mplstyle()` writes a style file and
    `register_mplstyles()` registers `paperplot-<journal>` into matplotlib's
    library — the **look only**. A style sheet structurally cannot size to the
    column, embed fonts, or preflight, so it is the entry point that graduates to
    `pp.figure()`/`pp.save()`, never a replacement. Registration is opt-in (never
    on import). File-text hex colors are emitted without `#` (a comment char in
    `.mplstyle`), matching matplotlib's own `matplotlibrc`.

---

## 2. Journal scope (v1): Physical Review (APS)

| Property | Value | Source / note |
|---|---|---|
| Single column | 8.6 cm (3.39 in, 86 mm) | APS Style Basics |
| Double column | 17.8 cm (7.01 in, 178 mm) | APS two-column letter |
| 1.5 column | ~12 cm (advisory, not a fixed APS spec) | "if detail requires" |
| Usable text height | ≈ 23.5 cm (configurable; minus caption for full-page) | US-letter + REVTeX |
| Min lettering | **2 mm cap height ⇒ ~7–8 pt font** (NOT 5.7 pt) | APS style guide |
| Min line weight | 0.5 pt (0.18 mm) | APS style guide |
| Color | **RGB submit; print is grayscale (H24)** — must stay legible in gray | APS H24 |
| Fonts | all embedded, **no Type-3**, `fonttype=42` for pdf+ps | APS/PDF checker |
| Resolution | vector preferred; rasterized sub-elements ≥600 dpi (line), ≥300 (photo) | APS |
| Formats | **EPS** (REVTeX-cleanest) + PDF first-class; PNG fallback; SVG = preview only | APS |

**Type defaults** (literal points only when included unscaled): base/axis-label
8 pt, ticks 7.5 pt, panel letters 9 pt bold, legend 7.5 pt. Floor derived from
the 2 mm cap-height rule (≈7–8 pt), **warned, never silently bumped**. Font floor
assumes placement at true width; a warning fires if the figure is later scaled.

---

## 3. Standard layouts

`Width` enum (string aliases accepted, case-normalized, validated with a
"did you mean" error): `SINGLE`, `ONEHALF`, `DOUBLE`, `FULL_PAGE`.

| `Width` | width (in) | height rule |
|---|---|---|
| `SINGLE` | 3.39 | golden, clamped to usable height |
| `ONEHALF` | 4.72 | golden, clamped |
| `DOUBLE` | 7.01 | golden, clamped |
| `FULL_PAGE` | 7.01 | **defaults to (usable height − caption reserve)**, not golden |

`height=` always overrides. The clamp is a **ceiling** on golden heights;
FULL_PAGE uses a page-height **default** so it actually fills the page.

---

## 4. Module layout

```
paperplot/
├── __init__.py        # façade (public API; see §6)
├── journals.py        # JournalSpec frozen dataclass + FontScale + variants
├── registry.py        # TOML load/validate/merge/cache; revision pinning  ← was implicit
├── data/journals.toml # the APS numbers (data) with schema_version + revisions
├── layout.py          # Width enum, figsize math, golden, page/caption clamp, units
├── style.py           # rcparams(spec,**ov); use()/style()/reset(); mathtext; fonts glue
├── lint.py            # preflight(spec, fig) -> Report; Type-3 / font / lw / cap-height /
│                      #   grayscale-luminance checks                        ← was check()
├── palettes.py        # qualitative cycle + sequential/diverging cmaps; custom reg;
│                      #   sequential-as-categorical guard; fills()/strokes()
├── plots.py           # opinionated composites: hist_outline/hist_filled,
│                      #   data_fit_band, swatches (matplotlib core; seaborn opt-in)
├── preview.py         # show(zoom); preview_in_page(mock page); grayscale_proof()
├── fonts.py           # register bundled license-clean sans (Liberation/TeX-Gyre/DejaVu)
└── save.py            # EPS/PDF/PNG/SVG; embed-all-fonts; alpha-in-EPS & fallback warnings;
                       #   rasterized-heavy-artist helper; runs preflight()
```

11 focused modules. `units` folded into `layout`. Public API is `__init__` +
documented symbols only; everything else is internal (leading-underscore-free but
not re-exported — explicit public/private contract in docs).

---

## 5. Core type & registry

```python
@dataclass(frozen=True, slots=True)
class JournalSpec:
    name: str                        # "Physical Review"
    revision: str                    # "2024-01"  ← reproducibility pin
    widths_mm: dict[str, float]
    page_height_mm: float
    caption_reserve_mm: float        # reserved when clamping FULL_PAGE
    font_family: tuple[str, ...]
    font_pt: FontScale               # base/tick/panel/legend + cap-height-derived min
    min_linewidth_pt: float          # 0.5
    rasterize_dpi: dict[str, int]    # sub-element dpi: {"line": 600, "photo": 300}

    def figsize(self, width, aspect=GOLDEN, height=None) -> tuple[float, float]: ...
    # NOTE: only pure, field-only geometry lives on the dataclass.
    # rcparams() lives in style.py; preflight() lives in lint.py — both free
    # functions taking the spec, so JournalSpec stays pure/testable data with no
    # matplotlib-Figure coupling.
```

**Registry (`registry.py`)** — the load-bearing layer between TOML and specs:
- TOML schema: `[journal.aps]` + `[journal.aps.font_pt]` subtable +
  `[journal.aps.variants.prl]` override tables.
- `schema_version` (format) + per-journal `revision` (content/date).
- List→tuple coercion (TOML has no tuple) for `font_family`.
- **Variant merge = shallow per-field override** with an explicit allowed-override
  set (not arbitrary deep merge; a variant cannot drop required keys).
- Unknown-key rejection; required-key validation; friendly errors.
- Loaded via `importlib.resources.files("paperplot.data")` (never `__file__`).
- Memoized: `get_spec("aps")` returns a cached singleton; `get_spec("aps@2024-01")`
  pins a revision. Prior revisions are retained, not overwritten.

---

## 6. Public API

```python
import paperplot as pp

pp.use("aps")                          # set active journal ONCE (scoped style applied)

# common case: no journal arg anywhere after use()
fig, ax = pp.figure(width="single")    # or pp.Width.SINGLE
ax.plot(df["delay_ns"], df["population"])
pp.save(fig, "fig1.eps")               # embeds fonts, runs preflight(), warns on issues

# multi-panel; figure() also makes grids (no separate subplots() needed to learn)
fig, axes = pp.figure(width="double", nrows=2, ncols=2)
pp.panel_labels(axes)                  # (a)(b)(c)(d), journal panel-letter style
pp.despine(axes)                       # native, no seaborn

# scoped override / multi-journal
with pp.style("aps", serif=True):
    fig, ax = pp.figure(width="full_page")
pp.reset()                             # restore prior rcParams

# colors
pp.register_palette("mylab", ["#e5f5f9", "#99d8c9", "#2ca25f"])  # categorical
fig, ax = pp.figure(width="single", palette="mylab")
cmap = pp.cmap("BuGn")                  # ordered/heatmap; palette() warns if you
                                        #   try to use a sequential scheme as a cycle

# notebook preview (optional extra: paperplot[notebook])
pp.show(fig, zoom=2)                    # magnified SVG; figure NOT mutated
pp.preview_in_page(fig, width="single") # figure embedded in mock journal page, true scale
pp.grayscale_proof(fig)                 # APS print reality check

# pre-submission lint (also auto-run by save)
report = pp.preflight(fig)             # structured Report, not list[str]
print(report)                          # "panel (c) y-label cap-height 1.7mm < 2mm APS min"
```

`figure()`/`subplots()` are the same maker (subplots is an alias). `use` = sticky
global; `style` = scoped; `reset` = restore. Tier-2 symbols (`palette`, `cmap`,
`register_palette`, `preview_in_page`, `grayscale_proof`, `panel_labels`,
`despine`) are documented under "and more."

---

## 7. Colors & palettes

- **Qualitative cycle** (categories) vs **sequential/diverging cmaps** (ordered) —
  strictly separate. Default cycle = **Okabe-Ito / colorblind-safe** (bundled hex,
  no seaborn needed). `palette="mpl"` restores `tab10`.
- **No hardcoded ColorBrewer hex** — wrapped from matplotlib's bundled colormaps.
- `palette(name, n)` **warns/refuses** on known-sequential/diverging names (the
  anti-pattern is enforced, not aspirational), using ColorBrewer type metadata.
- **Grayscale (APS H24):** `grayscale_proof()` renders desaturated; `preflight()`
  flags cycle colors that collapse to near-identical luminance. README documents
  the "(Color online)" + "red (dark gray)" caption convention.
- Custom palettes via `register_palette`; reserved names (`mpl`) can't be shadowed.

---

## 8. Notebook preview

- **`show(fig, zoom=2)`** — `savefig(buf, format="svg")` **without**
  `bbox_inches="tight"`, scales the SVG via width/height attrs, displays via lazy
  IPython import. On constrained/tight layout a draw runs, so the contract is
  "visually equivalent," achieved on a deep-copied figure to truly avoid mutation.
- **`preview_in_page(fig, width, page="letter", columns=2)`** — renders inner
  figure to SVG, places it via an inset at exact-inch extent
  (`inner_w_frac = fig_w_in / page_w_in`) on a faux two-column page. Documented
  caveat: true-scale only when the proof is viewed/printed at 100%; emits at a
  fixed dpi with the intended viewing size stated. Pure-matplotlib (no IPython).
- **`grayscale_proof(fig)`** — see §7.

---

## 9. Save / export (`save.py`)

- First-class **EPS** (true BoundingBox at literal column width) + **PDF**; PNG
  fallback; SVG = preview only (not an APS submission format).
- **Embed all fonts**: `pdf.fonttype=42`, `ps.fonttype=42`; **detect Type-3** in
  output and warn; warn when requested family fell back to DejaVu (embed guarantee
  becomes observable).
- **Warn on alpha<1 artists when target is EPS** (matplotlib rasterizes them).
- **`rasterized=True` helper** for dense imshow/scatter so heavy pixels stay small
  while text/axes stay vector — the standard APS big-data-figure trick.
- RGB is the default (matplotlib has no CMYK path) — stated, not promised as work.
- `save()` runs `preflight()` and surfaces actionable warnings; spec `revision`
  written into PDF/PNG metadata for reproducibility.

---

## 10. Cross-cutting contracts

- **Errors:** unknown journal/width/palette → friendly error listing valid options
  ("did you mean"). Missing font / non-embeddable font / figure-too-tall →
  explicit warnings, never silent.
- **Global-state lifecycle:** `style()` uses `rc_context` (restores on exception);
  `use()` snapshots prior rc for `reset()`; nesting precedence defined; matplotlib
  rcParams is process-global → **documented as not thread-safe**; a per-figure path
  avoids global rc.
- **Packaging:** `journals.toml` + bundled fonts declared as package data; loaded
  via `importlib.resources`. **Only redistributably-licensed fonts bundled**
  (DejaVu Sans, Liberation Sans, TeX-Gyre Heros). **Arial/Helvetica are runtime
  font-family *preferences*, never shipped files.** CI test loads the data file +
  every bundled font from the built wheel.
- **Reproducibility:** spec `revision` pinning + retained prior revisions +
  metadata stamping, so a 2024 figure re-renders identically in 2026.
- **Tests:** golden rcParams dicts; geometry asserted against the TOML numbers;
  `preflight` tested against known-bad figures; rcParams snapshot/restore fixture.

---

## 11. Planned deliverables beyond code

- README hero: 4-line quickstart + **before/after gallery** (the #1 adoption
  driver) + dependency/Python footprint.
- Verify PyPI name availability for `paperplot`; note `pp` alias collides with
  `pprint` — lead docs with full name or a safer alias.

---

## 12. Concrete rcParams mapping (the core translation layer)

`style.rcparams(spec, *, serif=False, usetex=False, palette=None)` builds the dict
below from a spec (shown for APS, base font 8 pt, min line 0.5 pt). This is the
core translation layer; values derive from spec fields, not magic constants.

```python
{
  # --- fonts ---
  "font.family":          "serif" if serif else "sans-serif",
  "font.sans-serif":      ["Arial", "Helvetica", "TeX Gyre Heros", "DejaVu Sans"],
  "font.serif":           ["Times", "Nimbus Roman", "DejaVu Serif"],
  "font.size":            spec.font_pt.base,        # 8
  "axes.labelsize":       spec.font_pt.base,        # 8
  "axes.titlesize":       spec.font_pt.base,        # 8
  "xtick.labelsize":      spec.font_pt.tick,        # 7.5
  "ytick.labelsize":      spec.font_pt.tick,        # 7.5
  "legend.fontsize":      spec.font_pt.legend,      # 7.5
  "legend.title_fontsize":spec.font_pt.base,        # 8
  "figure.titlesize":     spec.font_pt.base,        # 8
  # math: tied to text choice (or LaTeX preamble when usetex)
  "mathtext.fontset":     "cm" if serif else "dejavusans",
  "text.usetex":          usetex,
  "axes.unicode_minus":   not usetex,
  "axes.formatter.use_mathtext": True,
  # --- lines, ticks, spines (>= spec.min_linewidth_pt) ---
  "axes.linewidth":       max(0.6, spec.min_linewidth_pt),
  "lines.linewidth":      1.0,
  "lines.markersize":     3.0,
  "lines.markeredgewidth":0.5,
  "patch.linewidth":      0.6,
  "xtick.direction":      "in",   "ytick.direction": "in",
  "xtick.major.width":    spec.min_linewidth_pt,  "ytick.major.width": spec.min_linewidth_pt,
  "xtick.minor.width":    0.4,    "ytick.minor.width": 0.4,
  "xtick.major.size":     3.0,    "ytick.major.size":  3.0,
  "xtick.minor.size":     1.5,    "ytick.minor.size":  1.5,
  "xtick.major.pad":      3,      "ytick.major.pad":   3,
  "axes.titlepad":        3,      "axes.labelpad":     2,
  "axes.xmargin":         0.02,   "axes.ymargin":      0.02,
  # spines: top/right ON by default (APS full-box); pp.despine() removes them
  "axes.spines.top":      True,   "axes.spines.right": True,
  # --- color cycle ---
  "axes.prop_cycle":      cycler(color = palette or OKABE_ITO),
  # --- figure / save ---
  "figure.figsize":       spec.figsize("single"),   # bare plt.figure() is also correct
  "figure.facecolor":     "white",
  "figure.dpi":           150,                       # crisp notebook display
  "savefig.dpi":          spec.rasterize_dpi["line"],# 600 for raster sub-elements
  "savefig.bbox":         "standard",                # respect the chosen frame
  "savefig.pad_inches":   0.01,
  "savefig.transparent":  False,
  "pdf.fonttype":         42,
  "ps.fonttype":          42,
}
```

Open sub-decisions worth your call: **(a)** top/right spines ON (APS full-box,
shown above) vs OFF (cleaner, modern) by default; **(b)** `lines.linewidth` 1.0
vs 1.2; **(c)** notebook `figure.dpi` 150 vs leaving matplotlib's default.

## 13. `figure()` — full signature (the function every user touches first)

```python
def figure(
    width: Width | str = Width.SINGLE,         # "single"/"onehalf"/"double"/"full_page"
    *,
    aspect: float | Literal["golden", "equal"] | None = "golden",
    height: float | None = None,               # inches; OVERRIDES aspect when given
    nrows: int = 1,
    ncols: int = 1,
    journal: str | JournalSpec | None = None,  # per-call override of the use() journal
    palette: str | Sequence | None = None,     # per-figure color-cycle override
    serif: bool | None = None,                 # per-figure text-style override
    sharex: bool | Literal["row","col","all"] = False,
    sharey: bool | Literal["row","col","all"] = False,
    height_ratios: Sequence[float] | None = None,
    width_ratios: Sequence[float] | None = None,
    constrained: bool = True,                  # constrained_layout (modern spacing)
    **subplot_kw,                              # passthrough to plt.subplots / GridSpec
) -> tuple[Figure, Axes | np.ndarray]:
    ...

subplots = figure   # alias; mpl users reach for either, both make grids
```

**Return:** mirrors `plt.subplots` — a single `Axes` when `nrows == ncols == 1`,
otherwise an `ndarray[Axes]`. No new mental model to learn.

**Resolution order for journal/style:**
1. `journal=` arg → else the active journal from `pp.use(...)` → else a clear
   error ("No active journal; call `pp.use('aps')` or pass `journal=`").
2. `serif`/`palette` args override the active style for *this figure only*.

**Scoping mechanism (resolves the earlier scoped-vs-global hazard):** `figure()`
does **not** rely on global rcParams being correct. It computes the spec's style
and **applies the axes-level properties directly to the created axes** (label
sizes, tick params, spine widths, `prop_cycle`, frame) plus figure-level props to
the `Figure`. So every figure is internally self-consistent regardless of any
ambient `use()`/`style()` state — two figures with different `journal=` can
coexist in one session without desync. `use()`/`style()` still set rcParams so
that *ad-hoc* `ax.plot()` styling and bare `plt.figure()` are also correct.

**Sizing:**
- `figsize` width is fixed by `width` (the journal column width).
- `aspect` applies to the **whole figure bbox**: `"golden"` → h = w/φ; `"equal"`
  → h = w; a float → h = w·aspect. `height=` (inches) overrides `aspect`.
- `FULL_PAGE` ignores `aspect` and defaults to (usable height − caption reserve);
  `height=` still overrides. Golden heights are clamped to usable height.
- `height_ratios`/`width_ratios` drive uneven panel grids via `GridSpec`.

**Errors:** invalid `width`/`journal` strings raise `ValueError` listing valid
options ("did you mean 'single'?"). `aspect` and `height` both given → `height`
wins, with an info-level note.

**Example coverage:**
```python
pp.use("aps")
fig, ax    = pp.figure()                                   # single col, golden
fig, ax    = pp.figure("double", aspect="equal")           # square, 2-col
fig, ax    = pp.figure("single", height=2.2)               # explicit height
fig, axes  = pp.figure("double", nrows=2, ncols=2, sharex="col")
fig, axes  = pp.figure("full_page", nrows=4, height_ratios=[2,1,1,1])
fig, ax    = pp.figure("single", journal="prl", serif=True, palette="mylab")
```

## 14. `preflight()` Report shape (the moat, made concrete)

```python
@dataclass(frozen=True)
class Finding:
    severity: Literal["warn", "info"]     # warn-never-block → nothing raises
    rule: str            # min_cap_height | min_linewidth | font_type3 |
                         # font_fallback | gray_luminance | alpha_in_eps
    locator: str         # human: "axes[1] y-label", "legend", "Line2D #3"
    measured: float | str
    limit:    float | str
    message:  str        # "y-label cap-height 1.7 mm < 2.0 mm APS min"

@dataclass(frozen=True)
class Report:
    findings: tuple[Finding, ...]
    @property
    def ok(self) -> bool: ...            # no warn-level findings
    def __bool__(self): return self.ok
    def __str__(self): ...               # pretty aligned table for notebooks
    def by_rule(self, rule: str) -> tuple[Finding, ...]: ...
```

`preflight()` forces a draw on a **deep-copied** figure (so constrained_layout
can't mutate the user's figure), then inspects: tick labels via
`ax.get_xticklabels()` post-draw, axis labels, title, legend texts, annotations;
`Line2D` vs `Collection` linewidths; output-level Type-3 font scan; requested-font
fallback; and cycle-color grayscale luminance separation. Structured + queryable,
so CI can do `if not pp.preflight(fig): sys.exit(1)` while interactive users just
read the table.

## 15. Helpers & `FontScale` (the last details)

**`FontScale`** — point sizes + the APS cap-height floor:
```python
@dataclass(frozen=True)
class FontScale:
    base: float = 8.0      # axis labels, title, base
    tick: float = 7.5      # tick labels
    panel: float = 9.0     # (a)(b)(c) panel letters, bold
    legend: float = 7.5
    min_warn_pt: float = 7.0          # preflight warns below this (defaults pass)
    min_cap_height_mm: float = 2.0    # APS rule (informational in preflight)
    cap_height_ratio: float = 0.72    # cap-height / em for sans faces
    def cap_height_mm(self, pt: float) -> float:   # pt * 0.352777 * ratio
        ...
```
Defaults are chosen to **pass their own preflight** (7.5 ≥ 7.0) — your out-of-box
figure never warns about itself. The 2 mm cap-height rule is reported at info level
so you can tighten if a reviewer asks.

**`panel_labels(axes, labels=None, *, loc="upper left", weight="bold", size=None,
offset_pt=(2, 2), fmt="{}")`** — stamps `a, b, c…` (auto from `string.ascii_lowercase`)
on each axes via `ax.annotate` in axes-fraction coords with a points offset, so
labels align across panels regardless of axis size. `fmt="({})"` → `(a)`; `size`
defaults to `FontScale.panel`.

**`despine(axes, *, top=True, right=True, left=False, bottom=False)`** — removes the
named spines and their ticks (native, no seaborn). Default is the inverse of the
full-box style, so `despine(ax)` gives the clean L+B look on demand.

**`clean_shared_axes(fig)`** — on a shared grid, hides inner tick labels and
redundant axis labels, keeping them only on the outer row/column.
