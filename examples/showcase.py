"""paperplot showcase — a hands-on tour, from a stock plot to journal-ready figures.

This file doubles as a tutorial notebook (the ``# %%`` cells) and a plain script.
Run it cell by cell in VS Code / Jupyter / Colab, or all at once:
``python examples/showcase.py``. Each figure is saved as a publication **PDF** (via
``pp.save``, which runs preflight) and a **PNG** proof in ``examples/out/render/``.

Step by step you'll learn:
  - the two-call workflow: ``pp.use(journal)`` then ``pp.figure(width=...)``
  - real column-width sizing (APS / Nature / IEEE) and multi-panel layouts
  - switching journals — and a ``talk`` target — without touching plot code
  - color done right: the colorblind-safe cycle, colormaps, fills/strokes
  - composite helpers: ``hist_outline``, ``data_fit_band``
  - ``preflight()`` — catching sub-spec fonts/lines before you submit
  - seeing the figure *on the page* (``preview_in_page``) and grayscale proofing
  - typography: serif/REVTeX, math fonts, and one-knob font scaling
"""

# %% [markdown]
# Publication figures often fail review for dull reasons: the figure is the wrong
# width for the column, fonts aren't embedded, or the lettering is too small once
# it's scaled to fit. **paperplot** takes care of those. The entire workflow is two
# calls:
#
# 1. **`pp.use("aps")`** — pick the journal once (`"nature"`, `"ieee"`, `"prl"`, or
#    `"talk"` for slides). This sets the sizes, fonts, and line weights.
# 2. **`pp.figure(width="single")`** — get a figure already sized and styled to it.
#
# Every section below builds on those two lines. First, setup — on Colab the next
# cell installs paperplot; locally it just imports it.

# %% setup — install (Colab/Binder), imports, output folders, helpers
import os
import sys

# Run straight from a repo checkout, no `pip install` required (no-op once installed).
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
except NameError:
    pass  # running as a notebook cell — rely on the installed package instead

# On Colab / Binder paperplot isn't installed yet — install it on first run. (Safe
# to re-run; it's a no-op once importable. On Colab this is the only setup needed.)
try:
    import paperplot as pp
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                    "git+https://github.com/zlatko-minev/paperplot.git"], check=True)
    import paperplot as pp

import numpy as np

# Outputs land in the package's examples/out/ (PDFs) and out/render/ (PNG proofs).
# Anchored on paperplot's own location so paths resolve as a script, a notebook,
# or an installed copy alike.
_root = os.path.dirname(os.path.dirname(os.path.abspath(pp.__file__)))
OUT = os.path.join(_root, "examples", "out")
RENDER = os.path.join(OUT, "render")
os.makedirs(RENDER, exist_ok=True)


def save_both(fig, name):
    """Write the publication PDF (``pp.save`` runs preflight) plus a PNG proof."""
    report = pp.save(fig, os.path.join(OUT, name + ".pdf"))
    fig.savefig(os.path.join(RENDER, name + ".png"), dpi=200, facecolor="white")
    return report


def damped(t, k, tau=10.0):
    """Toy damped cosine — stand-in 'measurement' reused across the examples."""
    return np.exp(-t / tau) * np.cos(k * t)


print("paperplot ready ·", len(pp.available()), "journals:", ", ".join(pp.available()))
print("outputs →", OUT)

# %% [markdown]
# ## A quick look at the colors
# Before we plot, meet the palette system. paperplot's default cycle is the
# **colorblind-safe** Okabe-Ito set, and it ships a few more named palettes.
# `pp.show_palettes()` previews them all (colorblind-safe ones are tagged) and
# `pp.available_palettes()` lists their names. We'll lean on these throughout.

# %% palettes-overview
fig = pp.show_palettes()
fig.savefig(os.path.join(RENDER, "show_palettes.png"), dpi=200, facecolor="white")  # PNG proof only
print("palettes:", pp.available_palettes())

# %% [markdown]
# ## Your first figure — APS, single column
# The two calls in action. `pp.use("aps")` selects Physical Review; `pp.figure(
# width="single")` hands back a figure exactly **8.6 cm** wide (APS's single-column
# width) at a golden-ratio height, with APS fonts and line weights already applied.
# From here you just plot as usual.
#
# The cell also runs **`pp.preview_in_page`**, which drops the figure into a
# true-to-scale mock journal page — so you can see how big it actually lands in the
# column, and whether the lettering still reads, *before* you submit.

# %% aps-single
pp.use("aps")
t = np.linspace(0, 4 * np.pi, 400)

fig, ax = pp.figure(width="single")            # golden ratio by default
for k, lab in zip((1.0, 0.6, 0.3), ("Ground", "First", "Second")):
    ax.plot(t, damped(t, k), label=lab)
ax.set_xlabel(r"Delay $\tau$ (ns)")
ax.set_ylabel(r"Population $\langle n \rangle$")
ax.legend(frameon=False)
fig.savefig(os.path.join(RENDER, "aps_single.png"), dpi=200, facecolor="white")

fig2 = pp.preview_in_page(fig, width="single")


# %% [markdown]
# ## Going wide — double column
# `width="double"` gives the full **17.8 cm** two-column width. Here `aspect=0.32`
# overrides the golden ratio to make a short, wide panel — the shape you want for a
# spectrum or a long time trace. (Prefer an exact size? pass `height=` in inches.)

# %% aps-double
fig, ax = pp.figure(width="double", aspect=0.32)
x = np.linspace(0, 20, 1000)
for phase in np.linspace(0, np.pi, 5):
    ax.plot(x, np.sin(x + phase), lw=1.0)
ax.set_xlabel("Frequency (GHz)")
ax.set_ylabel("Transmission")
save_both(fig, "aps_double")

fig2 = pp.preview_in_page(fig, width="double")

# %% [markdown]
# ## Multi-panel layouts
# `pp.figure(nrows=2, ncols=2)` builds a grid that still fits the single column.
# Two helpers keep it tidy at that small size: `pp.panel_labels` stamps (a)(b)(c)(d)
# in the margin, and `pp.clean_shared_axes` removes the redundant inner tick labels
# on shared axes.

# %% aps-4panel
rng = np.random.default_rng(1)
fig, axes = pp.figure(width="single", nrows=2, ncols=2,
                      sharex=True, sharey=True)
for ax in axes.ravel():
    ax.plot(t, damped(t, rng.uniform(0.3, 1.2)), lw=1.0)
    ax.set_xlabel(r"$\tau$ (ns)")
    ax.set_ylabel(r"$\langle n \rangle$")
pp.panel_labels(axes, fmt="({})")   # outside top-left; first column nudged into the margin
pp.clean_shared_axes(fig)                       # inner labels removed
save_both(fig, "aps_4panel_single")

fig2 = pp.preview_in_page(fig, width="single")

# %% [markdown]
# ## Switch journals in one line
# Here's the payoff of choosing the journal once: the *same plotting code* retargets
# just by changing `pp.use`. `pp.use("nature")` applies Nature's narrower 7 pt type
# and 89 mm column automatically — nothing else in the cell changes. The same is
# true for `pp.use("ieee")` and, for slides, `pp.use("talk")` (bigger type, thicker
# lines).

# %% nature-single
pp.use("nature")
fig, ax = pp.figure(width="single")
for k, lab in zip((1.0, 0.6, 0.3), ("a", "b", "c")):
    ax.plot(t, damped(t, k), label=lab)
ax.set_xlabel(r"Delay $\tau$ (ns)")
ax.set_ylabel(r"Population $\langle n \rangle$")
ax.legend(frameon=False)
save_both(fig, "nature_single")

# %% [markdown]
# ## Heatmaps and ordered data
# A three-panel Nature double-column figure. For *ordered* data (images, heatmaps)
# reach for a sequential or diverging colormap via **`pp.cmap(...)`** — kept
# deliberately separate from the categorical cycle, which we'll come back to next.

# %% nature-double
fig, axes = pp.figure(width="double", ncols=3, aspect=1/(2*1.618))
for i, ax in enumerate(axes):
    img = np.outer(np.sin(np.linspace(0, (i + 1) * np.pi, 60)),
                   np.cos(np.linspace(0, np.pi, 60)))
    ax.imshow(img, cmap=pp.cmap("RdBu"), aspect="auto")
    ax.set_title(f"Mode {i + 1}")
pp.panel_labels(axes)
save_both(fig, "nature_double")

fig2 = pp.preview_in_page(fig, width="double")

# %% [markdown]
# ## Distributions that stay legible
# Bare `ax.hist` bars blur together at small sizes. **`pp.hist_outline`** draws a
# translucent fill under a crisp staircase **outline**, so each distribution still
# reads clearly — even four to a 2×2 grid at 89 mm.

# %% nature-4panel
fig, axes = pp.figure(width="single", nrows=2, ncols=2)
for ax, c in zip(axes.ravel(), pp.fills()):
    pp.hist_outline(rng.normal(size=400), ax, bins=18, color=c)
    ax.set_xlabel(r"$x$")
    ax.set_ylabel("Counts")
pp.panel_labels(axes)
pp.clean_shared_axes(fig)
save_both(fig, "nature_4panel_single")

fig2 = pp.preview_in_page(fig, width="double")

# %% [markdown]
# ## Color, done right
# Three things worth knowing:
#
# - **Categorical** data uses the colorblind-safe **Okabe-Ito** cycle by default.
# - **Ordered** data uses a colormap via **`pp.cmap(...)`** — never the categorical
#   cycle (paperplot warns if you try, because a sequential ramp read as categories
#   misleads the eye).
# - Bring your own categorical palette with **`pp.register_palette(name, colors)`**
#   and use it anywhere by name.

# %% colors
pp.use("aps")
pp.register_palette("mylab", ["#e5f5f9", "#99d8c9", "#2ca25f"])

fig, axes = pp.figure(width="double", ncols=3, aspect=0.33)
axes[0].set_title("Okabe-Ito (default)")
for c in pp.palette("okabe-ito"):
    axes[0].plot(t, damped(t, rng.uniform(0.3, 1.2)), color=c, lw=1.0)

axes[1].set_title("Custom 'mylab'")
axes[1].set_prop_cycle(color=pp.palette("mylab"))   # registered categorical palette
for _ in range(3):
    axes[1].plot(t, damped(t, rng.uniform(0.3, 1.2)), lw=1.2)

axes[2].set_title("Sequential cmap")
axes[2].imshow(np.add.outer(np.linspace(0, 1, 40), np.linspace(0, 1, 40)),
               cmap=pp.cmap("BuGn"), aspect="auto")
save_both(fig, "colors")

fig2 = pp.preview_in_page(fig, width="double")

# %% [markdown]
# ## The palette reference
# `pp.show_palettes()` again, on its own: an at-a-glance card of every categorical
# palette, each tagged colorblind-safe or not (`pp.is_colorblind_safe`). Palettes you
# register show up here too.

# %% palettes
fig = pp.show_palettes()
fig.savefig(os.path.join(RENDER, "palettes.png"), dpi=150,
            bbox_inches="tight", facecolor="white")

# %% [markdown]
# ## Layered figures: fills vs. strokes
# When you stack filled areas under lines, use **muted** colors for the fills and
# **bright** colors for the strokes on top so they don't compete. `pp.fills()` and
# `pp.strokes()` give you matched sets for exactly this; `pp.swatches` renders any
# palette as labeled chips.

# %% fills-strokes
fig = pp.swatches({"Fills() — muted": pp.fills(), "Strokes() — bright": pp.strokes()})
fig.savefig(os.path.join(RENDER, "fills_strokes.png"), dpi=150,
            bbox_inches="tight", facecolor="white")

# %% [markdown]
# ## Overlapping histograms
# The fills/strokes convention in practice: a muted fill per distribution, a bright
# dashed line for the reference value. `rescale=True` normalizes each peak to 1, so
# distributions of different sizes stay comparable.


# %% hist-overlap
fig, ax = pp.figure(width="single")
samples = {"Experiment": rng.normal(0.0, 1.0, 4000),
           "Control": rng.normal(1.4, 0.6, 4000)}
for (name, s), fc in zip(samples.items(), pp.fills()):
    pp.hist_outline(s, ax, bins=60, range=(-3, 4), rescale=True,
                    color=fc, label=name)
ax.axvline(-0.5, color=pp.strokes()[5], ls="--", lw=1.2, zorder=100,
           label=r"Target $\mu$")                    # bright dashed reference
ax.set_xlabel(r"Sampled $X_r$")
ax.set_ylabel("Empirical probability")
ax.set_ymargin(0)
ax.set_ylim(0, 1.08)
ax.legend(frameon=False)
save_both(fig, "hist_overlap")


fig2 = pp.preview_in_page(fig, width="single")

# %% [markdown]
# ## Data + fit + confidence band
# A standard results figure in a single call: error-barred markers, a fit line, and
# a translucent ±1σ band. Feed it your fitter's output — e.g. lmfit's `result.eval`
# for `y_fit` and `eval_uncertainty` for `y_fit_err`.

# %% data-fit-band
fig, ax = pp.figure(width="single")
xd = np.linspace(0.5, 5, 8)
true = 0.4 * np.exp(-xd / 1.6)
yd = true + rng.normal(0, 0.015, xd.size)
yerr = 0.02 * np.ones_like(xd)
xf = np.linspace(0.5, 5, 200)
yf = 0.4 * np.exp(-xf / 1.6)
yf_err = yf * (0.06 + 0.05 * xf)            # relative band: reads cleanly on log y
pp.data_fit_band(ax, xd, yd, yerr=yerr, x_fit=xf, y_fit=yf, y_fit_err=yf_err,
                 color=pp.strokes()[0], label="Data", fit_label="Exp. fit")
ax.set_xlabel(r"Independent variable $\nu$")
ax.set_ylabel(r"Measured value $y$")
ax.set_yscale("log")
ax.legend(frameon=False)
save_both(fig, "data_fit_band")

# %% [markdown]
# ## Preflight — catch problems before you submit
# `pp.preflight(fig)` checks a figure against the journal's rules and returns a
# structured report: sub-minimum fonts and line weights as **warnings**, the
# cap-height guideline and grayscale ambiguity as **info**. It never blocks — a clean
# figure passes, a deliberately broken one lists exactly what to fix — and `pp.save()`
# runs it for you on every export.

# %% preflight
fig, ax = pp.figure(width="single")
ax.plot(t, damped(t, 1.0))
ax.set_xlabel(r"$x$")
print("CLEAN figure:")
print(pp.preflight(fig))

bad, ax = pp.figure(width="single")
ax.plot(t, damped(t, 1.0), linewidth=0.2)       # below 0.5 pt
ax.set_xlabel("Too small", fontsize=4)           # below 7 pt
print("\nDELIBERATELY BAD figure:")
report = pp.preflight(bad)
print(report)
print("ok?", bool(report), "| linewidth findings:", len(report.by_rule("min_linewidth")))

# %% [markdown]
# ## See it on the page (and in grayscale)
# The checks a reviewer effectively does — run them yourself first:
#
# - **`pp.preview_in_page(fig)`** — the figure at true scale inside a mock journal
#   page with real body text, so "too big" or "lettering too small" jumps out early.
#   This is paperplot's signature move; most styling tools stop at the bare figure.
# - **`pp.show(fig, zoom=2)`** — a magnified inline preview (needs a notebook
#   front-end).
# - **`pp.grayscale_proof(fig)`** — how it reads in black-and-white print, where
#   colors that look distinct on screen can collapse to the same gray.

# %% preview
fig, ax = pp.figure(width="single")
for k in (1.0, 0.6, 0.3):
    ax.plot(t, damped(t, k))
ax.set_xlabel(r"Delay $\tau$ (ns)")
ax.set_ylabel(r"$\langle n \rangle$")

try:
    pp.show(fig, zoom=2)                          # renders inline in Jupyter
except ImportError:
    print("show() needs IPython (paperplot[notebook]) + a notebook front-end")

# justified lorem ipsum at true body size, with the figure boundary drawn
pp.preview_in_page(fig, width="single", figure_box=True).savefig(
    os.path.join(RENDER, "preview_in_page.png"), dpi=150, facecolor="white")
pp.grayscale_proof(fig).savefig(
    os.path.join(RENDER, "grayscale_proof.png"), dpi=150, facecolor="white")

# %% [markdown]
# ## Serif / REVTeX mode and EPS export
# `serif=True` switches to a Times-like serif body (matching REVTeX) with Computer
# Modern math. Wrapping it in `with pp.style(...)` applies the change **scoped** —
# rcParams are restored on exit, so it won't leak into later figures. `pp.save(...,
# ".eps")` writes EPS (first-class for REVTeX) with fonts embedded.

# %% serif-scoped-eps
with pp.style("aps", serif=True):                # scoped: doesn't leak out
    fig, ax = pp.figure(width="single", serif=True)
    ax.plot(t, damped(t, 1.0))
    ax.set_xlabel(r"$\Gamma / 2\pi$ (MHz)")        # math matches serif body
    ax.set_ylabel(r"$\hbar \omega$")
    pp.save(fig, os.path.join(OUT, "aps_serif.eps"))  # EPS first-class
    fig.savefig(os.path.join(RENDER, "aps_serif.png"), dpi=200, facecolor="white")

# %% [markdown]
# ## Math typography — the LaTeX look, no LaTeX needed
# Labels like `$\tau$` and `$\langle n \rangle$` are math. By default paperplot
# renders them in **Computer Modern** — the LaTeX look — over sans-serif text labels,
# **with no LaTeX install required**. Your options:
#
# - **`math="sans"`** — sans math (stixsans) to match Arial/Helvetica labels.
# - **`serif=True`** — Times body + Computer Modern math, for a REVTeX/serif paper.
# - **`usetex=True`** — render through a real LaTeX engine (needs LaTeX on PATH);
#   an exact REVTeX match, but slower to draw.
#
# The two panels below are the *same* plot — default CM math, then sans — so you can
# compare the glyphs directly (the italic τ, the angle brackets, the Σ).

# %% math-typography
def math_demo(ax):
    """Draw one labelled plot whose ticks, axis labels, and title all contain math."""
    ax.plot(t, damped(t, 1.0))
    ax.set_xlabel(r"Delay $\tau$ (ns)")
    ax.set_ylabel(r"Population $\langle n \rangle$")
    ax.set_title(r"$\hbar\omega = \sum_k \alpha_k\, e^{-t/\tau}$", fontsize=8)

# Default: sans-serif text labels with Computer Modern math (the LaTeX look).
pp.use("aps")
fig, ax = pp.figure(width="single")
math_demo(ax)
fig.savefig(os.path.join(RENDER, "math_default_cm.png"), dpi=200, facecolor="white")

# math="sans" — sans math (stixsans) that pairs with the Arial/Helvetica labels.
fig, ax = pp.figure(width="single", math="sans")
math_demo(ax)
fig.savefig(os.path.join(RENDER, "math_sans.png"), dpi=200, facecolor="white")

print("math typography → math_default_cm.png (default CM) · math_sans.png (sans)")

# %% [markdown]
# ## One knob for size, and fonts that travel
# `font_scale` multiplies every size at once — handy for a dense panel or a talk.
# preflight still warns if you scale *below* the journal minimum, so it's a nudge,
# not an escape hatch. Lettering uses Arial/Helvetica when installed, otherwise the
# bundled **TeX Gyre Heros** (a free, metric-compatible Helvetica clone) — so figures
# look the same on every machine and embed a real Type-42 font in the PDF.

# %% font-scale
pp.use("aps", font_scale=1.25)        # everything 25% larger; sticky for later calls
fig, ax = pp.figure(width="single")
ax.plot(t, damped(t, 1.0))
ax.set_xlabel(r"Delay $\tau$ (ns)")
ax.set_ylabel(r"Population $\langle n \rangle$")
save_both(fig, "font_scale_1p25")
pp.use("aps")                         # back to the journal default

print("\nAll showcase outputs written to", OUT)

# %% [markdown]
# ## Where to go next
# You've covered the whole workflow. A few things to keep handy:
#
# - **Saving:** `pp.save(fig, "f.pdf")` (default) or `"f.eps"` — fonts embedded,
#   preflight run, the journal revision stamped into the metadata.
# - **Just the look, no API:** `pp.register_mplstyles()` then
#   `plt.style.use("paperplot-aps")`, or write a file with
#   `pp.export_mplstyle("aps", "aps.mplstyle")`.
# - **More targets:** `pp.available()` lists them all; adding a journal is pure data
#   in `journals.toml` — no code.
#
# Full documentation: <https://zlatko-minev.github.io/paperplot/>

# %%
