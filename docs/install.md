# Installation

paperplot's core is **matplotlib-only** (just `numpy` + `matplotlib`). Python ≥ 3.10.
`seaborn` and `IPython` are optional extras, pulled in only if you ask for them.

We recommend **[uv](https://docs.astral.sh/uv/)** — one fast tool for environments
and installs. The other paths work just as well; pick whichever you already use.

=== "uv (recommended)"

    ```bash
    # into the current environment
    uv pip install paperplot                 # PyPI — coming soon (use GitHub for now)

    # …or add it to a uv-managed project
    uv add paperplot

    # with extras
    uv pip install "paperplot[notebook]"     # IPython, for pp.show()
    ```

    No environment yet? `uv venv && source .venv/bin/activate` first.

=== "pip (PyPI)"

    !!! note "Not on PyPI yet"
        The first release isn't published yet — use the **From GitHub** tab until then.

    ```bash
    pip install paperplot
    pip install "paperplot[notebook]"        # IPython, for pp.show()
    ```

=== "From GitHub"

    Install the latest `main` directly — no clone needed:

    ```bash
    uv pip install "git+https://github.com/zlatko-minev/paperplot.git"
    # or:
    pip install "git+https://github.com/zlatko-minev/paperplot.git"
    ```

=== "Clone (development)"

    For hacking on paperplot itself (tests, examples, docs):

    ```bash
    git clone https://github.com/zlatko-minev/paperplot.git
    cd paperplot
    uv pip install -e ".[dev]"               # editable + pytest
    pytest
    ```

## Optional extras

| Extra | Installs | Enables |
|---|---|---|
| `notebook` | IPython | `pp.show(fig, zoom=…)` inline preview |
| `seaborn` | seaborn | the opt-in seaborn path in `pp.hist_outline` |
| `docs` | mkdocs-material | building this site (`mkdocs serve`) |
| `dev` | pytest | the test suite |

Combine them with commas, e.g. `uv pip install "paperplot[notebook,seaborn]"`.

## Building the docs locally

```bash
uv pip install -e ".[docs,notebook]"
python docs/generate_gallery.py             # renders the showcase → gallery images
mkdocs serve                                # live preview at http://127.0.0.1:8000
```
