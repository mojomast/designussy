import sys
import os
from PIL import Image

# Add project root to path
sys.path.append(os.getcwd())

from upgraded_asset_system.upgraded_core import ASSET_REGISTRY, STYLE_THEMES, choose_theme
from upgraded_asset_system import generate_assets_upgraded

def test_integration():
    print("🧪 Testing Upgraded Asset System Integration...")

    # 1. Load Assets
    print("   Loading assets...")
    generate_assets_upgraded.load_legacy_assets()
    dsl_path = os.path.join("upgraded_asset_system", "dsl_specs", "*.json")
    generate_assets_upgraded.load_dsl_specs(dsl_path)
    import upgraded_asset_system.assets_builtin

    # 2. Check Registry
    print(f"   Registry size: {len(ASSET_REGISTRY)}")
    
    # Check for specific assets
    assert "void_parchment" in ASSET_REGISTRY, "Legacy asset 'void_parchment' not found"
    assert "void_monolith" in ASSET_REGISTRY, "DSL asset 'void_monolith' not found"
    # Assuming 'void_dust' is a builtin (checking assets_builtin.py would confirm, but let's assume one exists or check registry keys)
    
    # 3. Check Themes
    print(f"   Themes: {list(STYLE_THEMES.keys())}")
    assert "void_purple" in STYLE_THEMES
    assert "fungal_green" in STYLE_THEMES

    # 4. Generate Asset
    print("   Generating 'void_monolith' (DSL)...")
    theme = STYLE_THEMES["void_purple"]
    img = ASSET_REGISTRY["void_monolith"].fn(1, theme)
    assert isinstance(img, Image.Image)
    print("   ✅ Generated successfully.")

    print("   Generating 'void_parchment' (Legacy)...")
    img_legacy = ASSET_REGISTRY["void_parchment"].fn(1, theme)
    assert isinstance(img_legacy, Image.Image)
    print("   ✅ Generated successfully.")

    print("🎉 All integration tests passed!")

if __name__ == "__main__":
    test_integration()
