"""Robustness regression tests: colormap API, palette guards, preflight noise,
save() side-effects, registry merges, and previously-untested public surface."""

import matplotlib
matplotlib.use("Agg")

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.collections import LineCollection

import paperplot as pp


@pytest.fixture(autouse=True)
def _clean_rc():
    snap = dict(mpl.rcParams)
    yield
    pp.reset()
    mpl.rcParams.update(snap)
    plt.close("all")


# --- #1 cm.get_cmap removal / modern colormaps API ---------------------------

def test_cmap_uses_modern_api_no_attributeerror():
    cm = pp.cmap("viridis")              # would AttributeError on mpl>=3.9 with old code
    assert cm.N > 0


def test_palette_qualitative_colormap_works():
    cols = pp.palette("Set2")           # routes through colormaps[...]
    assert 1 < len(cols) <= 12
    assert len(set(cols)) > 1


# --- #2 qualitative heuristic: continuous maps are bounded + warned ----------

def test_palette_continuous_map_warns_and_is_bounded():
    with pytest.warns(UserWarning, match="anti-pattern"):
        cols = pp.palette("turbo")      # 256-entry ListedColormap in modern mpl
    assert len(cols) <= 8               # NOT a 256-color dump


def test_palette_sequential_name_still_warns():
    with pytest.warns(UserWarning, match="anti-pattern"):
        pp.palette("viridis", 3)


def test_palette_unknown_raises():
    with pytest.raises(ValueError):
        pp.palette("definitely_not_a_palette_or_cmap_xyz")


# --- #3 / #10 preflight is silent on the shipped defaults --------------------

def test_default_figure_preflight_is_silent():
    pp.use("aps")
    fig, ax = pp.figure(width="single")
    ax.plot([0, 1], [0, 1])
    ax.set_xlabel("x")
    report = pp.preflight(fig)
    assert report.ok
    assert report.by_rule("gray_luminance") == ()   # default cycle not nagged
    assert report.by_rule("min_font") == ()          # default sizes not nagged


def test_low_contrast_custom_cycle_still_flagged():
    pp.use("aps", palette=["#000000", "#050505"])    # near-identical in gray
    fig, ax = pp.figure(width="single")
    ax.plot([0, 1], [0, 1])
    report = pp.preflight(fig)
    assert report.by_rule("gray_luminance")


# --- #11 preflight catches thin collection linewidths ------------------------

def test_preflight_flags_thin_linecollection():
    pp.use("aps")
    fig, ax = pp.figure(width="single")
    ax.add_collection(LineCollection([[(0, 0), (1, 1)]], linewidths=0.1))
    report = pp.preflight(fig)
    assert any(f.rule == "min_linewidth" and "collection" in f.locator
               for f in report.findings)


# --- #9 save() does not mutate global rcParams -------------------------------

def test_save_does_not_clobber_global_fonttype(tmp_path):
    pp.use("aps")
    fig, ax = pp.figure(width="single")
    ax.plot([0, 1], [0, 1])
    mpl.rcParams["pdf.fonttype"] = 3        # sentinel the caller set
    pp.save(fig, tmp_path / "x.pdf")
    assert mpl.rcParams["pdf.fonttype"] == 3   # save scoped its 42 via rc_context


# --- #12 EPS/PS alpha warning broadened --------------------------------------

def test_eps_alpha_warns_for_fill_between(tmp_path):
    pp.use("aps")
    fig, ax = pp.figure(width="single")
    ax.fill_between([0, 1, 2], [0, 1, 0], alpha=0.3)   # RGBA alpha, not artist.alpha
    with pytest.warns(UserWarning, match="rasterizes"):
        pp.save(fig, tmp_path / "a.eps", run_preflight=False)


def test_ps_alpha_warns_too(tmp_path):
    pp.use("aps")
    fig, ax = pp.figure(width="single")
    ax.fill_between([0, 1, 2], [0, 1, 0], alpha=0.3)
    with pytest.warns(UserWarning, match="rasterizes"):
        pp.save(fig, tmp_path / "a.ps", run_preflight=False)


# --- #7 registry deep-merges nested variant overrides ------------------------

def test_deep_merge_keeps_sibling_nested_fields():
    from paperplot.registry import _deep_merge
    merged = _deep_merge({"font_pt": {"base": 8.0, "tick": 7.5}},
                         {"font_pt": {"base": 9.0}})
    assert merged["font_pt"] == {"base": 9.0, "tick": 7.5}


# --- #8 panel_labels never runs out of letters -------------------------------

def test_default_labels_past_26():
    from paperplot.core import _default_labels
    labs = _default_labels(30)
    assert len(labs) == 30 and len(set(labs)) == 30
    assert labs[:3] == ["a", "b", "c"] and labs[26] == "aa"


# --- #4 smoke coverage for previously-untested public surface ----------------

def test_despine_hides_named_spines():
    pp.use("aps")
    fig, ax = pp.figure(width="single")
    pp.despine(ax)
    assert ax.spines["top"].get_visible() is False
    assert ax.spines["right"].get_visible() is False
    assert ax.spines["left"].get_visible() is True


def test_preview_helpers_return_figures_without_mutating():
    pp.use("aps")
    fig, ax = pp.figure(width="single")
    ax.plot([0, 1], [0, 1])
    page = pp.preview_in_page(fig, width="single")
    proof = pp.grayscale_proof(fig)
    assert page is not None and page is not fig
    assert proof is not None and proof is not fig


# --- #21 the one seaborn touchpoint (optional extra) -------------------------

def test_hist_outline_seaborn_path():
    pytest.importorskip("seaborn")
    pp.use("aps")
    fig, ax = pp.figure(width="single")
    data = np.random.default_rng(0).normal(size=200)
    out_ax, (counts, edges) = pp.hist_outline(data, ax, bins=10, use_seaborn=True)
    assert out_ax is ax
    assert len(ax.lines) >= 1   # staircase outline is always matplotlib


# --- #20 font fallback contract (host-independent) ---------------------------

def test_available_family_returns_none_when_nothing_present():
    from paperplot import fonts
    assert fonts.available_family(["NoSuchFont__123", "AlsoMissing__456"]) is None
