"""Test script to generate diverse assets with new prefix"""
import sys
sys.path.insert(0, '.')

from generate_assets import (
    create_void_crystal,
    create_mystic_eye,
    create_rune_stone,
    create_ancient_key,
    create_broken_chain,
    create_mystic_frame,
    create_void_hopper,
    create_abyssal_jelly,
    create_void_manta,
    save_asset,
    CATEGORIES
)

# Generate 3 test variants for each asset type
print("Generating test assets to demonstrate diversity...")

asset_generators = [
    ('void_crystal', create_void_crystal, 'backgrounds'),
    ('mystic_eye', create_mystic_eye, 'glyphs'),
    ('rune_stone', create_rune_stone, 'glyphs'),
    ('ancient_key', create_ancient_key, 'ui'),
    ('broken_chain', create_broken_chain, 'ui'),
    ('mystic_frame', create_mystic_frame, 'ui'),
    ('void_hopper', create_void_hopper, 'creatures'),
    ('abyssal_jelly', create_abyssal_jelly, 'creatures'),
    ('void_manta', create_void_manta, 'creatures'),
]

for asset_name, generator_func, category in asset_generators:
    print(f"\nGenerating test_{asset_name}...")
    for i in range(1, 4):
        img = generator_func(index=None)  # Generate without index to avoid auto-save
        save_asset(img, category, f"test_{asset_name}", i)

print("\n✅ Done! Check assets/static/elements/ for test_* files")
