"""Font registration.

Only redistributably-licensed faces would ever be *bundled* (DejaVu/Liberation/
TeX-Gyre Heros); Arial/Helvetica are runtime *preferences*, never shipped here.
If a ``data/fonts`` directory exists, its fonts are registered; otherwise this is
a silent no-op and matplotlib's resolution + the spec's fallback chain apply.
"""

from __future__ import annotations

from importlib.resources import files

from matplotlib import font_manager

_done = False


def register_bundled(verbose: bool = False) -> int:
    """Register any bundled fonts. Idempotent. Returns the count added."""
    global _done
    if _done:
        return 0
    _done = True
    try:
        font_dir = files("paperplot").joinpath("data", "fonts")
        if not font_dir.is_dir():
            return 0
        added = 0
        for path in font_manager.findSystemFonts(fontpaths=[str(font_dir)]):
            font_manager.fontManager.addfont(path)
            if verbose:
                print(f"registered {path}")
            added += 1
        return added
    except (FileNotFoundError, OSError):
        return 0


def available_family(preferences) -> str | None:
    """Return the first font family from ``preferences`` actually installed."""
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for fam in preferences:
        if fam in installed:
            return fam
    return None
