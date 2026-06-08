"""Tests for the plot helpers (paperplot.plots) and the fill/stroke palettes."""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

import paperplot as pp
from paperplot import palettes


@pytest.fixture(autouse=True)
def _clean_rc():
    snap = dict(matplotlib.rcParams)
    yield
    pp.reset()
    matplotlib.rcParams.update(snap)
    plt.close("all")


@pytest.fixture
def data():
    rng = np.random.default_rng(0)
    return rng.normal(size=2000)


# --- fill / stroke palettes --------------------------------------------------

def test_fills_strokes_are_distinct_and_long():
    assert pp.fills()[:1] != pp.strokes()[:1]
    assert len(pp.fills()) >= 6 and len(pp.strokes()) >= 6
    assert all(c.startswith("#") for c in pp.fills() + pp.strokes())


def test_named_palettes_resolve():
    assert pp.palette("muted") == palettes.MUTED
    assert pp.palette("bright") == palettes.BRIGHT
    assert pp.palette("colorblind")[0] == palettes.COLORBLIND[0]


def test_fills_n_cycles():
    assert len(pp.fills(3)) == 3
    assert len(pp.fills(20)) == 20  # wraps past the 10 base colors


def test_available_palettes_lists_builtins_and_custom():
    pp.register_palette("mylab_test", ["#000000", "#ffffff"])
    names = pp.available_palettes()
    assert "okabe-ito" in names
    assert {"muted", "bright", "colorblind"} <= set(names)
    assert "mylab_test" in names


def test_colorblind_safe_flags():
    assert pp.is_colorblind_safe("okabe-ito")
    assert pp.is_colorblind_safe("okabe_ito")   # underscore variant
    assert pp.is_colorblind_safe("colorblind")
    assert not pp.is_colorblind_safe("muted")
    assert not pp.is_colorblind_safe("bright")


# --- hist_outline ------------------------------------------------------------

def test_hist_outline_returns_counts_and_draws(data):
    pp.use("aps")
    fig, ax = pp.figure(width="single")
    out_ax, (counts, edges) = pp.hist_outline(data, ax, bins=30, label="x")
    assert out_ax is ax
    assert len(counts) == 30 and len(edges) == 31
    # one fill (PolyCollection) + one outline (Line2D)
    assert len(ax.collections) == 1
    assert len(ax.lines) == 1


def test_hist_outline_rescale_peak_is_one(data):
    pp.use("aps")
    _, ax = pp.figure(width="single")
    _, (counts, _) = pp.hist_outline(data, ax, bins=40, rescale=True)
    assert counts.max() == pytest.approx(1.0)


def test_hist_outline_no_fill_outline_carries_label(data):
    pp.use("aps")
    _, ax = pp.figure(width="single")
    pp.hist_outline(data, ax, fill=False, label="only-line")
    assert len(ax.collections) == 0
    assert ax.lines[0].get_label() == "only-line"


def test_hist_outline_creates_axes_when_none(data):
    pp.use("aps")
    ax, _ = pp.hist_outline(data, bins=10)
    assert ax is not None


# --- hist_filled -------------------------------------------------------------

def test_hist_filled_returns_centers(data):
    pp.use("aps")
    _, ax = pp.figure(width="single")
    counts, edges, centers = pp.hist_filled(data, ax, bins=25, rescale=True)
    assert len(centers) == 25 and len(edges) == 26
    assert counts.max() == pytest.approx(1.0)
    assert len(ax.collections) == 1 and len(ax.lines) == 1


# --- data_fit_band -----------------------------------------------------------

def test_data_fit_band_data_only():
    pp.use("aps")
    _, ax = pp.figure(width="single")
    x = np.arange(5.0)
    pp.data_fit_band(ax, x, x * 2, yerr=np.ones(5))
    assert len(ax.lines) >= 1  # errorbar makes line/marker artists


def test_data_fit_band_with_fit_and_band():
    pp.use("aps")
    _, ax = pp.figure(width="single")
    x = np.linspace(0, 4, 6)
    xf = np.linspace(0, 4, 50)
    yf = np.exp(-xf)
    pp.data_fit_band(ax, x, np.exp(-x), yerr=0.05 * np.ones(6),
                     x_fit=xf, y_fit=yf, y_fit_err=0.02 * np.ones(50),
                     label="data", fit_label="fit")
    from matplotlib.collections import PolyCollection
    assert any(isinstance(c, PolyCollection) for c in ax.collections)  # the band
    assert any(ln.get_label() == "fit" for ln in ax.lines)  # the fit line


# --- swatches ----------------------------------------------------------------

def test_swatches_list_and_dict():
    fig = pp.swatches(pp.fills())
    assert fig is not None
    fig2 = pp.swatches({"fills": pp.fills(), "strokes": pp.strokes()})
    assert fig2 is not None


def test_show_palettes_renders_all_with_tags():
    fig = pp.show_palettes()
    assert fig is not None
    ax = fig.axes[0]
    texts = [t.get_text() for t in ax.texts]
    assert "okabe-ito" in texts and "muted" in texts
    assert any("colorblind-safe" in t for t in texts)  # at least one ✓ tag


def test_show_palettes_accepts_subset():
    fig = pp.show_palettes(["muted", "bright"])
    labels = {t.get_text() for t in fig.axes[0].texts}
    assert {"muted", "bright"} <= labels
