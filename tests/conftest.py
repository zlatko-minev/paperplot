"""Shared test config: Agg backend + a guard against mplstyle library leakage."""

import matplotlib
matplotlib.use("Agg")

import matplotlib.style as mstyle
import pytest


@pytest.fixture(autouse=True)
def _no_style_library_leak():
    """Remove any styles a test registers (e.g. via pp.register_mplstyles)."""
    before = set(mstyle.library)
    yield
    for name in list(mstyle.library):
        if name not in before:
            del mstyle.library[name]
