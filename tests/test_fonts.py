"""Tests for the bundled Helvetica clone (TeX Gyre Heros) and its registration."""

import matplotlib
matplotlib.use("Agg")

from matplotlib import font_manager as fm

from paperplot import fonts


def test_texgyreheros_is_bundled():
    """The OTFs ship in the package so the Helvetica look is deterministic."""
    from importlib.resources import files
    font_dir = files("paperplot").joinpath("data", "fonts")
    assert font_dir.is_dir()
    otfs = [p for p in font_dir.iterdir() if str(p).endswith(".otf")]
    assert len(otfs) >= 1


def test_register_bundled_makes_heros_available():
    fonts.register_bundled()
    names = {f.name for f in fm.fontManager.ttflist}
    assert "TeX Gyre Heros" in names


def test_register_bundled_is_idempotent():
    # _done guard means a second call adds nothing.
    fonts.register_bundled()
    assert fonts.register_bundled() == 0


def test_heros_is_the_fallback_when_arial_absent():
    fonts.register_bundled()
    # With no Arial/Helvetica in the chain, the bundled clone is chosen.
    assert fonts.available_family(["TeX Gyre Heros", "DejaVu Sans"]) == "TeX Gyre Heros"
