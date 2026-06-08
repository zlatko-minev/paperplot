"""Load journal specs from ``data/journals.toml`` into ``JournalSpec`` objects.

This is the layer between TOML and the frozen dataclasses: it reads the data
file via ``importlib.resources``, coerces types (TOML lists -> tuples), merges
variant overrides over their base, validates, and caches the result.
"""

from __future__ import annotations

import difflib
from functools import lru_cache
from importlib.resources import files
from typing import Dict

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # Python 3.10 backport
    import tomli as tomllib  # type: ignore

from .journals import FontScale, JournalSpec

_REQUIRED = {
    "name",
    "revision",
    "widths_mm",
    "page_height_mm",
    "caption_reserve_mm",
    "min_linewidth_pt",
    "font_family",
    "font_pt",
    "rasterize_dpi",
}


def _read_data() -> dict:
    text = files("paperplot").joinpath("data", "journals.toml").read_text("utf-8")
    return tomllib.loads(text)


def _deep_merge(base: dict, over: dict) -> dict:
    """Recursively merge ``over`` onto ``base`` so a variant can override a single
    nested field (e.g. font_pt.base) without dropping its siblings."""
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _build_spec(d: dict) -> JournalSpec:
    missing = _REQUIRED - d.keys()
    if missing:
        raise ValueError(f"Journal spec {d.get('name', '?')!r} missing keys: {sorted(missing)}")
    return JournalSpec(
        name=d["name"],
        revision=d["revision"],
        widths_mm={k: float(v) for k, v in d["widths_mm"].items()},
        page_height_mm=float(d["page_height_mm"]),
        caption_reserve_mm=float(d["caption_reserve_mm"]),
        font_family=tuple(d["font_family"]),  # TOML list -> tuple
        font_pt=FontScale(**d["font_pt"]),
        min_linewidth_pt=float(d["min_linewidth_pt"]),
        page_body_pt=float(d.get("page_body_pt", 10.0)),
        rasterize_dpi={k: int(v) for k, v in d["rasterize_dpi"].items()},
    )


@lru_cache(maxsize=1)
def _registry() -> Dict[str, JournalSpec]:
    data = _read_data()
    specs: Dict[str, JournalSpec] = {}
    for key, raw in data.get("journal", {}).items():
        variants = raw.pop("variants", {}) if isinstance(raw, dict) else {}
        base = _build_spec(raw)
        specs[key.lower()] = base
        for vkey, override in variants.items():
            # deep per-field override so a partial nested table (e.g. just
            # font_pt.base) keeps the base journal's sibling values.
            merged = _deep_merge(raw, override)
            specs[vkey.lower()] = _build_spec(merged)
    return specs


def available() -> list[str]:
    """Sorted list of known journal keys (including variants)."""
    return sorted(_registry())


def get_spec(key: str) -> JournalSpec:
    """Look up a spec by key, e.g. ``"aps"`` or ``"prl"``.

    A ``"key@revision"`` suffix is accepted and validated against the spec's
    own revision (reproducibility pin).
    """
    name, _, revision = str(key).strip().lower().partition("@")
    reg = _registry()
    try:
        spec = reg[name]
    except KeyError:
        hint = difflib.get_close_matches(name, reg, n=1)
        suffix = f" Did you mean {hint[0]!r}?" if hint else ""
        raise KeyError(
            f"Unknown journal {key!r}. Available: {available()}.{suffix}"
        ) from None
    if revision and revision != spec.revision.lower():
        raise ValueError(
            f"Journal {name!r} is revision {spec.revision!r}, not {revision!r}."
        )
    return spec
