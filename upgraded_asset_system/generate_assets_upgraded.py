
"""
generate_assets_upgraded.py

High-level CLI / entrypoint that:

- Imports the upgraded core/DSL system.
- Loads and registers new builtin assets.
- Optionally wraps your original generate_assets.py asset functions into the
  plugin registry (if that module is importable).
- Optionally loads DSL specs from ./dsl_specs/*.json.
- Calls generate_all_assets(...) to render everything.

You can integrate this file into your repo alongside your original
generate_assets.py and start using the upgraded system immediately.

Usage example (from project root, with venv activated):

    python -m generate_assets_upgraded --start 1 --end 21 --load-legacy --load-dsl

"""

import argparse
import glob
import importlib
import json
import os
from typing import List

try:
    from .upgraded_core import (
        ASSET_REGISTRY,
        register_asset,
        generate_all_assets,
        CATEGORIES,
    )
    from . import assets_builtin  # noqa: F401  - registers itself via decorators
    from .asset_dsl import register_spec
except ImportError:
    # Fallback for running directly as a script
    from upgraded_core import (
        ASSET_REGISTRY,
        register_asset,
        generate_all_assets,
        CATEGORIES,
    )
    import assets_builtin  # noqa: F401
    from asset_dsl import register_spec


# ---------------------------------------------------------------------------
# Legacy integration
# ---------------------------------------------------------------------------

LEGACY_CATEGORY_MAP = {
    # backgrounds
    "create_void_parchment": "backgrounds",
    "create_ink_nebula": "backgrounds",
    "create_ethereal_mist": "backgrounds",
    "create_floating_island": "backgrounds",
    # glyphs / frames / sigils
    "create_ink_enso": "glyphs",
    "create_sigil": "glyphs",
    "create_ink_divider": "glyphs",
    "create_void_orb": "glyphs",
    "create_mystic_eye": "glyphs",
    "create_rune_stone": "glyphs",
    "create_mystic_frame": "glyphs",
    "create_void_crystal": "glyphs",
    "create_void_rune": "glyphs",
    "create_ink_spiral": "glyphs",
    "create_ethereal_feather": "glyphs",
    "create_astral_eye": "glyphs",
    "create_void_circuit": "glyphs",
    "create_spectral_serpent": "glyphs",
    "create_void_portal": "glyphs",
    # creatures
    "create_giraffe": "creatures",
    "create_kangaroo": "creatures",
    "create_void_manta": "creatures",
    "create_ink_crab": "creatures",
    "create_void_hopper": "creatures",
    "create_abyssal_jelly": "creatures",
    "create_ink_butterfly": "creatures",
    # ui-ish
    "create_broken_chain": "ui",
    "create_ancient_key": "ui",
}


def load_legacy_assets():
    """
    Try to import your original generate_assets module and wrap its create_*
    asset functions into the new registry.

    This assumes the original file is named generate_assets.py and is
    importable on PYTHONPATH (e.g. same directory as this file).
    """
    try:
        legacy = importlib.import_module("generate_assets")
    except Exception as exc:  # pragma: no cover - optional
        print(f"[upgraded] Skipping legacy import (generate_assets not found: {exc})")
        return

    for attr_name in dir(legacy):
        if not attr_name.startswith("create_"):
            continue
        if attr_name == "create_noise_layer":
            continue
        fn = getattr(legacy, attr_name)
        if not callable(fn):
            continue

        category = LEGACY_CATEGORY_MAP.get(attr_name)
        if category is None:
            # Default to glyphs if not mapped (you can expand the map above).
            category = "glyphs"

        asset_name = attr_name.replace("create_", "")
        print(f"[upgraded] Wrapping legacy asset {attr_name} -> {asset_name} ({category})")

        @register_asset(asset_name, category, tags=["legacy"])
        def _wrapped(index=None, theme=None, _fn=fn):
            # Ignore theme for legacy assets; they do their own colors.
            return _fn(index)

    print(f"[upgraded] Legacy wrapper complete. Total assets now: {len(ASSET_REGISTRY)}")


# ---------------------------------------------------------------------------
# DSL loading
# ---------------------------------------------------------------------------

def load_dsl_specs(path_pattern: str = "dsl_specs/*.json"):
    """
    Load all JSON specs in the provided glob pattern and register them.
    """
    paths = sorted(glob.glob(path_pattern))
    for p in paths:
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            spec = register_spec(data)
            print(f"[upgraded] Registered DSL asset '{spec.name}' from {p}")
        except Exception as exc:  # pragma: no cover - data dependent
            print(f"[upgraded] Failed to load DSL spec from {p}: {exc}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    ap = argparse.ArgumentParser(description="Upgraded NanoBanana asset generator")
    ap.add_argument("--start", type=int, default=1, help="First index (inclusive)")
    ap.add_argument("--end", type=int, default=21, help="Last index (exclusive)")
    ap.add_argument(
        "--categories",
        type=str,
        nargs="*",
        default=None,
        help="Optional list of categories to generate (backgrounds, glyphs, creatures, ui)",
    )
    ap.add_argument(
        "--themes",
        type=str,
        nargs="*",
        default=None,
        help="Optional list of style theme names to cycle through",
    )
    ap.add_argument("--load-legacy", action="store_true", help="Wrap existing generate_assets.py assets")
    ap.add_argument("--load-dsl", action="store_true", help="Load JSON specs from ./dsl_specs")
    return ap.parse_args()


def main():
    args = parse_args()

    if args.load_legacy:
        load_legacy_assets()
    if args.load_dsl:
        load_dsl_specs()

    cats = args.categories
    if cats:
        cats = [c for c in cats if c in CATEGORIES]
    generate_all_assets(range(args.start, args.end), categories=cats, themes=args.themes, verbose=True)


if __name__ == "__main__":
    main()
