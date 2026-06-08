# paperplot — notes for agents

Publication-correct matplotlib figures, sized/styled/preflighted per journal
(APS + Nature + IEEE, plus a `talk` presentation target). Small library; keep it small.

## Commands
- Tests: `pytest` (Agg backend; fixtures snapshot/restore rcParams — keep that pattern).
- Examples: `python examples/showcase.py` or `python examples/run_all.py`
  → writes PDFs to `examples/out/` and PNG proofs to `examples/out/render/` (gitignored).
- Dev install: `pip install -e ".[dev]"`. Python ≥ 3.10.

## Hard rules (don't break these)
- **matplotlib-only core.** `numpy` + `matplotlib` are the only runtime deps.
  `seaborn` and `IPython` are OPTIONAL extras — import them lazily *inside* the
  function that needs them, behind a try/guard. Never add a top-level `import
  seaborn`/`IPython`. (`plots.hist_outline` has the one opt-in seaborn path.)
- **Journals are data, not code.** Add/edit journal specs in
  `paperplot/data/journals.toml`, loaded via `registry.py` — not hardcoded.
- **`__init__.py` is the public API contract.** Anything users call must be
  re-exported there and listed in `__all__`. Keep imports + `__all__` in sync.
- **`plots.py` is a deliberately small set** of opinionated composites
  (hist_outline/hist_filled, data_fit_band, swatches/show_palettes). It is NOT a
  general plotting library — no dataframes, faceting, or grammar-of-graphics.
  See the "Scope amendment" note in `paperplot_DESIGN.md`.
- **preflight warns, never blocks.** `save()`/`preflight()` always produce output
  and surface a `Report`; no raising/strict mode.
- **`.mplstyle` export is an on-ramp, not the product.** `mplstyle.py` renders the
  *look* (rcParams) for `plt.style.use`; it cannot size/embed/preflight, so never
  route core sizing through it. `register_mplstyles()` mutates matplotlib's global
  style library — keep it opt-in; NEVER auto-register on import (silent first import).
  Hex colors in the file text are written without `#` (it's a comment char there).

## Conventions
- Default cycle is **Okabe-Ito** (colorblind-safe). Separately, the fill/stroke
  convention: `pp.fills()` (muted) for areas, `pp.strokes()` (bright) for lines —
  these are NOT colorblind-safe; don't make them the categorical default.
- Sequential/diverging colormaps go through `pp.cmap(...)`, never the categorical
  cycle (palettes.py enforces this with a warning).

## Source of truth
`paperplot_DESIGN.md` records the design decisions and trade-offs — read it before
changing architecture (registry/versioning, rcParams mapping, journal model).
