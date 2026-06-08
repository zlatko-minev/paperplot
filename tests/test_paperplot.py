"""Tests for paperplot. Uses the Agg backend (no display)."""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

import paperplot as pp
from paperplot import layout
from paperplot.registry import get_spec


@pytest.fixture(autouse=True)
def _clean_rc():
    """Snapshot/restore rcParams so tests don't leak global state."""
    snap = dict(matplotlib.rcParams)
    yield
    pp.reset()
    matplotlib.rcParams.update(snap)
    plt.close("all")


# --- specs / registry --------------------------------------------------------

def test_aps_geometry():
    spec = get_spec("aps")
    assert spec.name == "Physical Review"
    assert spec.widths_mm["single"] == 86.0
    assert spec.widths_mm["double"] == 178.0
    assert spec.min_linewidth_pt == 0.5


def test_variants_inherit_geometry():
    aps, prl = get_spec("aps"), get_spec("prl")
    assert prl.widths_mm == aps.widths_mm
    assert prl.revision != aps.revision  # variant overrides revision


def test_nature_geometry():
    spec = get_spec("nature")
    assert spec.name == "Nature"
    assert spec.widths_mm["single"] == 89.0
    assert spec.widths_mm["double"] == 183.0
    assert spec.font_pt.base == 7.0


def test_nature_full_page_height_capped():
    spec = get_spec("nature")
    _, h = spec.figsize("full_page")
    assert h == pytest.approx(170.0 / 25.4, abs=1e-3)  # Nature max figure height


def test_unknown_journal_suggests():
    with pytest.raises(KeyError, match="Did you mean"):
        get_spec("apz")


def test_revision_pin():
    assert get_spec("aps@2024-01").name == "Physical Review"
    with pytest.raises(ValueError):
        get_spec("aps@1999-01")


# --- geometry ----------------------------------------------------------------

def test_single_width_inches():
    spec = get_spec("aps")
    w, h = spec.figsize("single")
    assert w == pytest.approx(86.0 / 25.4, abs=1e-3)  # 3.39 in
    assert h == pytest.approx(w / layout.GOLDEN, abs=1e-3)


def test_aspect_equal_and_explicit_height():
    spec = get_spec("aps")
    w, h = spec.figsize("double", aspect="equal")
    assert w == pytest.approx(h)
    w2, h2 = spec.figsize("single", height=2.2)
    assert h2 == pytest.approx(2.2)


def test_full_page_fills_height():
    spec = get_spec("aps")
    w, h = spec.figsize("full_page")
    expected = (spec.page_height_mm - spec.caption_reserve_mm) / 25.4
    assert h == pytest.approx(expected, abs=1e-3)
    assert h > w  # taller than wide, unlike a golden single column


def test_bad_width_suggests():
    with pytest.raises(ValueError, match="Did you mean"):
        layout.resolve_width("signle")


# --- style / figure ----------------------------------------------------------

def test_use_sets_rcparams():
    pp.use("aps")
    assert matplotlib.rcParams["font.size"] == 8.0
    assert matplotlib.rcParams["pdf.fonttype"] == 42


def test_figure_size_matches_spec():
    pp.use("aps")
    fig, ax = pp.figure(width="single")
    w, h = fig.get_size_inches()
    assert w == pytest.approx(86.0 / 25.4, abs=1e-3)


def test_figure_grid_returns_array():
    pp.use("aps")
    fig, axes = pp.figure(width="double", nrows=2, ncols=2)
    assert axes.shape == (2, 2)


def test_figure_without_journal_raises():
    with pytest.raises(RuntimeError):
        pp.figure(width="single")


def test_reset_restores():
    before = matplotlib.rcParams["font.size"]
    pp.use("aps")
    pp.reset()
    assert matplotlib.rcParams["font.size"] == before


# --- colors ------------------------------------------------------------------

def test_default_palette_is_okabe_ito():
    assert pp.palette("okabe-ito")[0] == "#0072B2"


def test_register_and_use_custom_palette():
    pp.register_palette("mylab", ["#e5f5f9", "#99d8c9", "#2ca25f"])
    assert pp.palette("mylab", 2) == ["#e5f5f9", "#99d8c9"]


def test_sequential_as_cycle_warns():
    with pytest.warns(UserWarning, match="anti-pattern"):
        pp.palette("BuGn", 3)


def test_reserved_palette_name_rejected():
    with pytest.raises(ValueError):
        pp.register_palette("mpl", ["#000000"])


# --- lint --------------------------------------------------------------------

def test_preflight_clean_default_figure():
    pp.use("aps")
    fig, ax = pp.figure(width="single")
    ax.plot([0, 1], [0, 1])
    ax.set_xlabel("x")
    report = pp.preflight(fig)
    assert report.ok  # defaults pass their own preflight
    assert bool(report) is True


def test_preflight_flags_tiny_font_and_thin_line():
    pp.use("aps")
    fig, ax = pp.figure(width="single")
    ax.plot([0, 1], [0, 1], linewidth=0.2)
    ax.set_xlabel("x", fontsize=4)
    report = pp.preflight(fig)
    assert not report.ok
    assert report.by_rule("min_linewidth")
    assert any(f.rule == "min_font" and f.severity == "warn" for f in report.findings)


# --- save --------------------------------------------------------------------

def test_save_defaults_to_pdf(tmp_path):
    pp.use("aps")
    fig, ax = pp.figure(width="single")
    ax.plot([0, 1], [0, 1])
    out = tmp_path / "fig"
    pp.save(fig, out)
    assert (tmp_path / "fig.pdf").exists()


def test_save_runs_preflight(tmp_path):
    pp.use("aps")
    fig, ax = pp.figure(width="single")
    ax.plot([0, 1], [0, 1])
    report = pp.save(fig, tmp_path / "ok.pdf")
    assert report is not None and report.ok


# --- math font (decoupled from serif) ----------------------------------------

def test_default_math_is_cm_with_sans_text():
    pp.use("aps")                                   # sans labels...
    assert matplotlib.rcParams["font.family"] == ["sans-serif"]
    assert matplotlib.rcParams["mathtext.fontset"] == "cm"   # ...but CM math


def test_math_sans_maps_to_stixsans():
    pp.use("aps", math="sans")
    assert matplotlib.rcParams["mathtext.fontset"] == "stixsans"


def test_math_auto_follows_text_family():
    pp.use("aps", math="auto")
    assert matplotlib.rcParams["mathtext.fontset"] == "stixsans"  # sans text
    pp.use("aps", math="auto", serif=True)
    assert matplotlib.rcParams["mathtext.fontset"] == "cm"        # serif text


def test_active_options_are_sticky_across_figure():
    pp.use("aps", serif=True, math="sans")
    pp.figure(width="single")                       # no kwargs -> must inherit
    assert matplotlib.rcParams["font.family"] == ["serif"]
    assert matplotlib.rcParams["mathtext.fontset"] == "stixsans"


def test_figure_overrides_active_options():
    pp.use("aps", math="cm")
    pp.figure(width="single", math="sans")
    assert matplotlib.rcParams["mathtext.fontset"] == "stixsans"


# --- font_scale --------------------------------------------------------------

def test_font_scale_multiplies_spec_sizes():
    spec = get_spec("aps")
    pp.use("aps", font_scale=1.5)
    assert matplotlib.rcParams["axes.labelsize"] == pytest.approx(spec.font_pt.base * 1.5)
    assert matplotlib.rcParams["xtick.labelsize"] == pytest.approx(spec.font_pt.tick * 1.5)


def test_font_scale_default_is_unity():
    spec = get_spec("aps")
    pp.use("aps")
    assert matplotlib.rcParams["axes.labelsize"] == pytest.approx(spec.font_pt.base)


def test_font_scale_down_still_preflight_warns():
    # Scaling below the journal minimum must still be flagged (absolute floor).
    pp.use("nature", font_scale=0.5)                # 7pt base -> 3.5pt
    fig, ax = pp.figure(width="single")
    ax.set_xlabel("x")
    report = pp.preflight(fig)
    assert any(f.rule == "min_font" and f.severity == "warn" for f in report.findings)


def test_reset_clears_active_options():
    pp.use("aps", math="sans", font_scale=2.0)
    pp.reset()
    pp.use("aps")                                   # fresh -> back to defaults
    assert matplotlib.rcParams["mathtext.fontset"] == "cm"
    assert matplotlib.rcParams["axes.labelsize"] == pytest.approx(get_spec("aps").font_pt.base)


# --- IEEE + talk targets ------------------------------------------------------

def test_ieee_geometry():
    spec = get_spec("ieee")
    assert spec.name == "IEEE"
    assert spec.width_in("single") == pytest.approx(3.5, abs=1e-2)   # 3.5" column
    assert spec.width_in("double") == pytest.approx(7.16, abs=2e-2)  # 7.16" text width
    assert "ieee" in pp.available()


def test_talk_scales_lines_and_fonts():
    from paperplot.style import rcparams
    talk, aps = rcparams(get_spec("talk")), rcparams(get_spec("aps"))
    # APS (min 0.5pt) keeps the publication defaults; talk (min 1.0pt) thickens.
    assert aps["lines.linewidth"] == 1.0 and aps["lines.markersize"] == 3.0
    assert talk["lines.linewidth"] == 2.0 and talk["lines.markersize"] == 6.0
    assert talk["font.size"] > aps["font.size"]


# --- .mplstyle on-ramp -------------------------------------------------------

def test_export_mplstyle_round_trips_through_matplotlib(tmp_path):
    import warnings
    path = tmp_path / "aps.mplstyle"
    pp.export_mplstyle("aps", str(path))
    with warnings.catch_warnings():
        warnings.simplefilter("error")              # any parse warning -> failure
        with plt.style.context(str(path)):
            cycle = matplotlib.rcParams["axes.prop_cycle"].by_key()["color"]
    assert cycle[0].lower() == "#0072b2"            # Okabe-Ito survives the round-trip


def test_mplstyle_text_writes_hex_without_hash():
    # '#' is a comment char in .mplstyle, so the cycle must use bare hex.
    text = pp.to_mplstyle_text("aps")
    line = next(l for l in text.splitlines() if l.startswith("axes.prop_cycle"))
    assert "'0072B2'" in line and "'#0072B2'" not in line


def test_register_mplstyles_is_opt_in_and_composable():
    import matplotlib.style as mstyle
    saved = dict(mstyle.library)
    try:
        names = pp.register_mplstyles()
        assert "paperplot-aps" in names and "paperplot-ieee" in names
        assert "paperplot-nature" in plt.style.available
        with plt.style.context("paperplot-nature"):
            assert matplotlib.rcParams["font.size"] == pytest.approx(7.0)
    finally:
        mstyle.library.clear()
        mstyle.library.update(saved)
        mstyle.available[:] = sorted(mstyle.library)
