"""Generate the documentation gallery.

Single source of truth for the gallery images, run both locally and in CI before
``mkdocs build``:

    python docs/generate_gallery.py

It (1) renders every showcase figure headless via ``examples/run_all.py``,
(2) builds the before/after hero (plain matplotlib vs. paperplot, same data),
(3) copies a curated subset into ``docs/assets/gallery/`` — the committed,
README-and-site-visible set — and (4) converts ``examples/showcase.py`` into an
executed ``docs/showcase.ipynb`` (code + output, with Colab/Binder links) that the
site renders via mkdocs-jupyter. ``examples/out/`` stays gitignored; the curated
gallery and the notebook are tracked.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")  # headless

import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

RENDER = os.path.join(ROOT, "examples", "out", "render")
GALLERY = os.path.join(HERE, "assets", "gallery")
SHOWCASE_PY = os.path.join(ROOT, "examples", "showcase.py")
SHOWCASE_IPYNB = os.path.join(HERE, "showcase.ipynb")

REPO = "zlatko-minev/paperplot"
NOTEBOOK_PATH = "docs/showcase.ipynb"  # path within the repo, for Colab/Binder

# Leading cell: title + one-click run links. Colab opens the committed .ipynb from
# GitHub; Binder builds the env from binder/requirements.txt and opens the same file.
BADGES_MD = f"""# paperplot showcase

Every figure below is produced by [`examples/showcase.py`](https://github.com/{REPO}/blob/main/examples/showcase.py)
— this page is that script, executed. Run it yourself, no install needed:

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/{REPO}/blob/main/{NOTEBOOK_PATH})
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/{REPO}/main?labpath={NOTEBOOK_PATH})
"""

# Curated set copied from the showcase render into the tracked gallery. Order is
# the display order on the gallery page.
CURATED = [
    ("aps_single.png", "APS, single column (8.6 cm)"),
    ("aps_4panel_single.png", "APS, 4-panel single column"),
    ("nature_double.png", "Nature, double column (183 mm)"),
    ("hist_overlap.png", "Overlapping outlined histograms"),
    ("data_fit_band.png", "Data + fit + confidence band"),
    ("colors.png", "Okabe-Ito, custom palette, sequential cmap"),
    ("math_default_cm.png", "Math: Computer Modern (default)"),
    ("math_sans.png", "Math: sans (stixsans)"),
    ("preview_in_page.png", "preview_in_page() — true on-page scale"),
    ("grayscale_proof.png", "grayscale_proof() — print legibility"),
]


def render_examples() -> None:
    """Run the showcase headless so examples/out/render/*.png exist and are fresh."""
    subprocess.run([sys.executable, os.path.join(ROOT, "examples", "run_all.py")],
                   check=True, cwd=ROOT)


def make_before_after() -> str:
    """Render the headline before/after: identical data, matplotlib vs. paperplot."""
    import paperplot as pp

    t = np.linspace(0, 4 * np.pi, 400)
    series = [(1.0, "Ground"), (0.6, "First"), (0.3, "Second")]

    def damped(k):
        return np.exp(-t / 10.0) * np.cos(k * t)

    # --- BEFORE: stock matplotlib defaults ---
    with plt.style.context("default"):
        fig_b, ax = plt.subplots()  # default 6.4x4.8 in, tab10, no journal sizing
        for k, lab in series:
            ax.plot(t, damped(k), label=lab)
        ax.set_xlabel(r"Delay $\tau$ (ns)")
        ax.set_ylabel(r"Population $\langle n \rangle$")
        ax.set_title("matplotlib defaults")
        ax.legend()
        before = os.path.join(GALLERY, "before.png")
        fig_b.savefig(before, dpi=200, bbox_inches="tight", facecolor="white")
        plt.close(fig_b)

    # --- AFTER: paperplot, APS single column ---
    pp.use("aps")
    fig_a, ax = pp.figure(width="single")
    for k, lab in series:
        ax.plot(t, damped(k), label=lab)
    ax.set_xlabel(r"Delay $\tau$ (ns)")
    ax.set_ylabel(r"Population $\langle n \rangle$")
    ax.set_title("paperplot — pp.use('aps')")
    ax.legend(frameon=False)
    after = os.path.join(GALLERY, "after.png")
    fig_a.savefig(after, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig_a)
    pp.reset()
    return "before.png + after.png"


def copy_curated() -> list[str]:
    copied = []
    for name, _ in CURATED:
        src = os.path.join(RENDER, name)
        if not os.path.exists(src):
            print(f"  ! missing {name} (showcase did not produce it)", file=sys.stderr)
            continue
        shutil.copyfile(src, os.path.join(GALLERY, name))
        copied.append(name)
    return copied


def _save_in_page(pp, fig, width, name) -> None:
    """Render ``fig`` inside a true-to-scale mock journal page and save it."""
    page = pp.preview_in_page(fig, width=width, figure_box=True)
    page.savefig(os.path.join(GALLERY, name), dpi=150,
                 bbox_inches="tight", facecolor="white")
    plt.close(fig)
    plt.close(page)


def make_in_page_previews() -> str:
    """Showcase the differentiator: several figures shown *in the page* via
    ``preview_in_page`` (figure dropped into mock body text at true column scale)."""
    import paperplot as pp

    rng = np.random.default_rng(1)
    t = np.linspace(0, 4 * np.pi, 400)

    def damped(k):
        return np.exp(-t / 10.0) * np.cos(k * t)

    pp.use("aps")
    out = []

    # 1) APS single-column line plot, in page.
    fig, ax = pp.figure(width="single")
    for k, lab in zip((1.0, 0.6, 0.3), ("Ground", "First", "Second")):
        ax.plot(t, damped(k), label=lab)
    ax.set_xlabel(r"Delay $\tau$ (ns)")
    ax.set_ylabel(r"Population $\langle n \rangle$")
    ax.legend(frameon=False)
    _save_in_page(pp, fig, "single", "in_page_aps.png")
    out.append("in_page_aps.png")

    # 2) Overlapping outlined histograms, in page.
    fig, ax = pp.figure(width="single")
    samples = {"Control": rng.normal(0.0, 1.0, 4000),
               "Braiding": rng.normal(1.4, 0.6, 4000)}
    for (name, s), fc in zip(samples.items(), pp.fills()):
        pp.hist_outline(s, ax, bins=60, range=(-3, 4), rescale=True,
                        color=fc, label=name)
    ax.axvline(1.618, color=pp.strokes()[8], ls="--", lw=1.2, zorder=100,
               label=r"Ideal $\phi$")
    ax.set_xlabel(r"Ratio $P_1/P_0$")
    ax.set_ylabel("Relative probability")
    ax.set_ymargin(0)
    ax.set_ylim(0, 1.08)
    ax.legend(frameon=False)
    _save_in_page(pp, fig, "single", "in_page_hist.png")
    out.append("in_page_hist.png")

    # 3) Data + fit + confidence band, in page.
    fig, ax = pp.figure(width="single")
    xd = np.linspace(0.5, 5, 8)
    xf = np.linspace(0.5, 5, 200)
    yd = 0.4 * np.exp(-xd / 1.6) + rng.normal(0, 0.015, xd.size)
    yf = 0.4 * np.exp(-xf / 1.6)
    pp.data_fit_band(ax, xd, yd, yerr=0.02 * np.ones_like(xd), x_fit=xf, y_fit=yf,
                     y_fit_err=yf * (0.06 + 0.05 * xf),
                     color=pp.strokes()[0], label="Data", fit_label="Exp. fit")
    ax.set_xlabel(r"Noise amplification $\lambda$")
    ax.set_ylabel("Expectation value")
    ax.set_yscale("log")
    ax.legend(frameon=False)
    _save_in_page(pp, fig, "single", "in_page_fit.png")
    out.append("in_page_fit.png")

    # 4) Double-column figure spanning both text columns, in page.
    fig, axes = pp.figure(width="double", ncols=3, aspect=1 / (2 * 1.618))
    for i, ax in enumerate(axes):
        img = np.outer(np.sin(np.linspace(0, (i + 1) * np.pi, 60)),
                       np.cos(np.linspace(0, np.pi, 60)))
        ax.imshow(img, cmap=pp.cmap("RdBu"), aspect="auto")
        ax.set_title(f"Mode {i + 1}")
    pp.panel_labels(axes)
    _save_in_page(pp, fig, "double", "in_page_double.png")
    out.append("in_page_double.png")

    pp.reset()
    return " + ".join(out)


def build_notebook() -> str:
    """Convert showcase.py -> docs/showcase.ipynb (unexecuted, with run links).

    The committed notebook is kept *clean* (no outputs) so it stays a few KB —
    ideal for Colab/Binder, where the reader runs it. mkdocs-jupyter executes it at
    build time (``execute: true``) so the rendered site still shows code + output.
    """
    import jupytext
    import nbformat

    # Register a python3 kernelspec so mkdocs-jupyter can execute the notebook
    # during the build (CI runners may not ship one).
    subprocess.run([sys.executable, "-m", "ipykernel", "install", "--user",
                    "--name", "python3"], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    nb = jupytext.read(SHOWCASE_PY)
    nb.cells.insert(0, nbformat.v4.new_markdown_cell(BADGES_MD))
    nbformat.write(nb, SHOWCASE_IPYNB)
    return os.path.relpath(SHOWCASE_IPYNB, ROOT)


def main() -> int:
    os.makedirs(GALLERY, exist_ok=True)
    print("Rendering showcase figures…")
    render_examples()
    print("Building before/after hero…")
    print("  ->", make_before_after())
    print("Copying curated gallery…")
    copied = copy_curated()
    print("Rendering in-page previews (the preview_in_page differentiator)…")
    print("  ->", make_in_page_previews())
    print(f"Gallery ready: {len(copied)} curated + before/after + in-page -> {GALLERY}")
    print("Building showcase notebook (clean; executed at docs-build time)…")
    print("  ->", build_notebook())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
