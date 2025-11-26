"""Generate samples of the 10 new asset types"""
import sys
import os

from generate_assets import (
    create_void_portal, create_spectral_wisp, create_ancient_scroll,
    create_shadow_beast, create_mystic_constellation, create_ink_butterfly,
    create_void_anchor, create_ethereal_torch, create_crystal_shard,
    create_runic_circle
)

print("Generating samples of 10 new asset types...")

new_generators = [
    ('void_portal', create_void_portal, 'glyphs'),
    ('spectral_wisp', create_spectral_wisp, 'creatures'),
    ('ancient_scroll', create_ancient_scroll, 'ui'),
    ('shadow_beast', create_shadow_beast, 'creatures'),
    ('mystic_constellation', create_mystic_constellation, 'glyphs'),
    ('ink_butterfly', create_ink_butterfly, 'creatures'),
    ('void_anchor', create_void_anchor, 'ui'),
    ('ethereal_torch', create_ethereal_torch, 'ui'),
    ('crystal_shard', create_crystal_shard, 'backgrounds'),
    ('runic_circle', create_runic_circle, 'glyphs'),
]

# Generate 3 variants with different seeds for each
for name, func, category in new_generators:
    print(f"\nGenerating new_{name}...")
    for i, seed_index in enumerate([50, 150, 250], 1):
        img = func(index=seed_index)
        
        # Rename to new_ prefix
        old_path = f"assets/static/elements/{category}/{name}_{seed_index}.png"
        new_path = f"assets/static/elements/{category}/new_{name}_{i}.png"
        
        if os.path.exists(old_path):
            if os.path.exists(new_path):
                os.remove(new_path)
            os.rename(old_path, new_path)
            print(f"  ✓ Created {new_path}")

print("\n✅ All new asset samples generated!")
