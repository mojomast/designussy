"""Test script to generate diverse assets with test_ prefix"""
import os
import sys

# Temporarily modify the save function to use test_ prefix
original_output_base = None

def setup_test_mode():
    """Setup test mode to save with test_ prefix"""
    global original_output_base
    import generate_assets
    # We'll generate the assets manually
    
if __name__ == "__main__":
    from generate_assets import (
        create_void_crystal, create_mystic_eye, create_rune_stone,
        create_ancient_key, create_broken_chain, create_mystic_frame,
        create_void_hopper, create_abyssal_jelly, create_void_manta
    )
    
    print("Generating test assets with diversity...")
    
    # Define which assets to generate
    generators = [
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
    
    # Generate 3 variants with different indices
    for name, func, category in generators:
        print(f"\nGenerating test_{name}...")
        # Use indices 100, 200, 300 to ensure very different seeds
        for i, seed_index in enumerate([100, 200, 300], 1):
            img = func(index=seed_index)  # This auto-saves with the seed_index
            
            # Now rename the file to test_ prefix
            old_path = f"assets/static/elements/{category}/{name}_{seed_index}.png"
            new_path = f"assets/static/elements/{category}/test_{name}_{i}.png"
            
            if os.path.exists(old_path):
                # Remove old test file if exists
                if os.path.exists(new_path):
                    os.remove(new_path)
                os.rename(old_path, new_path)
                print(f"  ✓ Created {new_path}")
    
    print("\n✅ All test assets generated with diversity!")
