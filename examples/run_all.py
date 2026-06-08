"""Run every paperplot example headless and render all figures to examples/out/render/.

The examples double as VS Code / Jupyter notebooks (``# %%`` cells, the occasional
IPython magic). This runner tolerates those notebook-isms — line/cell magics are
blanked out and ``display``/``get_ipython`` are stubbed — so the same files also
render in one shot with no external tools or install.

Usage::

    python examples/run_all.py
"""

import glob
import os
import re
import sys

import matplotlib

matplotlib.use("Agg")  # headless: write files, never pop a window

# The examples print Unicode (→, ·, σ…); Windows consoles default to cp1252 and
# would raise UnicodeEncodeError. Force UTF-8 output where the stream allows it.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))  # repo root, for `import paperplot`

_MAGIC = re.compile(r"\s*%{1,2}\w")  # IPython line/cell magic (invalid plain Python)


def _run(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    # Blank magic lines (keep line numbers intact for tracebacks).
    src = "\n".join("" if _MAGIC.match(ln) else ln for ln in lines)
    g = {"__name__": "__main__", "__file__": path,
         "display": lambda *a, **k: None, "get_ipython": lambda: None}
    exec(compile(src, path, "exec"), g)


scripts = [
    f for f in sorted(glob.glob(os.path.join(HERE, "*.py")))
    if os.path.basename(f) != "run_all.py"
]

for script in scripts:
    print(f"\n=== running {os.path.basename(script)} ===")
    _run(script)

pngs = sorted(glob.glob(os.path.join(HERE, "out", "render", "*.png")))
print(f"\nRendered {len(pngs)} image(s) to examples/out/render/:")
for p in pngs:
    print("  -", os.path.basename(p))
