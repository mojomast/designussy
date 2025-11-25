# Asset Directory Structure

## Overview

This document describes the organized asset directory structure for the voidussy project, designed for clarity and maintainability.

## Directory Structure

```
assets/
├── static/              # Pre-made, non-generated assets
│   ├── effects/         # Static effect images (ink_splatter.png, etc.)
│   ├── elements/        # Static element images organized by type
│   │   ├── backgrounds/ # Static background textures
│   │   ├── creatures/   # Static creature illustrations
│   │   ├── glyphs/      # Static glyphs and symbols
│   │   └── ui/          # Static UI elements (dividers, orbs, etc.)
│   └── ui/              # (Reserved for future static UI assets)
├── generated/           # Procedurally generated assets
│   ├── backgrounds/     # Generated parchment textures
│   ├── creatures/       # Generated creatures (giraffes, kangaroos)
│   ├── glyphs/          # Generated sigils and enso circles
│   └── ui/              # (Reserved for future generated UI elements)
├── css/                 # Stylesheets
│   ├── unwritten_worlds_common.css  # Shared component library
│   └── unwritten_worlds.css         # Legacy core styles (deprecated)
└── js/                  # JavaScript files
    ├── unwritten_worlds_common.js   # Shared component library
    └── unwritten_worlds_core.js     # Legacy core JS (deprecated)
```

## Directory Purposes

### `/static/` - Pre-made Assets

**Purpose**: Contains all manually created, non-generated assets.

**Subdirectories**:
- **`effects/`**: Core visual effect images that define the project's aesthetic
  - `ink_splatter.png` - Ink splatter overlay texture
  - `parchment.png` - Parchment background texture
  - `ouroboros.png` - Ouroboros spinner graphic
  - `runes.png` - Runic symbol texture

- **`elements/`**: Static element images organized by category
  - **`backgrounds/`**: Pre-made background textures (void_parchment_*.png)
  - **`creatures/`**: Static creature illustrations (giraffes, kangaroos)
  - **`glyphs/`**: Static symbols (enso circles, sigils)
  - **`ui/`**: UI elements (dividers, orbs)

**When to use**: For assets that are:
- Manually designed or edited
- Need to maintain exact appearance
- Used as reference or template images
- Not procedurally generated

### `/generated/` - Procedural Assets

**Purpose**: Contains all procedurally generated assets created by the voidussy generator.

**Subdirectories**:
- **`backgrounds/`**: Generated parchment textures (void_parchment_*.png)
- **`creatures/`**: Generated creature illustrations (giraffes, kangaroos)
- **`glyphs/`**: Generated symbols (enso circles, sigils)
- **`ui/`**: (Reserved for future generated UI elements)

**When to use**: For assets that are:
- Generated programmatically
- Created via the `generate_assets.py` script
- Served by the backend API
- Intended to be unique variations

### `/css/` - Stylesheets

**Purpose**: Contains all CSS stylesheets for the project.

**Files**:
- **`unwritten_worlds_common.css`**: Shared component library with all common styles
  - Design system variables
  - Typography rules
  - Layout utilities
  - Component styles
  - Animation keyframes
  - SVG filter helpers

- **`unwritten_worlds.css`**: Legacy core styles (deprecated, kept for backward compatibility)

**When to use**: 
- Reference `unwritten_worlds_common.css` in all HTML files
- Avoid using `unwritten_worlds.css` in new work

### `/js/` - JavaScript Files

**Purpose**: Contains all JavaScript files for the project.

**Files**:
- **`unwritten_worlds_common.js`**: Shared component library with all common functionality
  - SVG filter injection
  - API interaction helpers
  - Asset loading utilities
  - Settings management
  - Modal management
  - DOM manipulation helpers
  - Animation utilities
  - Event handling utilities

- **`unwritten_worlds_core.js`**: Legacy core JS (deprecated, kept for backward compatibility)

**When to use**:
- Reference `unwritten_worlds_common.js` in all HTML files
- Avoid using `unwritten_worlds_core.js` in new work

## Migration Guide

### For Future Changes

When adding new assets or reorganizing:

1. **Determine asset type**:
   - Is it manually created? → `/static/`
   - Is it procedurally generated? → `/generated/`
   - Is it a stylesheet? → `/css/`
   - Is it JavaScript? → `/js/`

2. **Choose appropriate subdirectory**:
   - Effects (textures, overlays) → `effects/`
   - Backgrounds → `backgrounds/`
   - Creatures → `creatures/`
   - Symbols/glyphs → `glyphs/`
   - UI elements → `ui/`

3. **Update references**:
   - Update HTML files that reference the asset
   - Update CSS files if used in `url()` references
   - Update the migration script if restructuring

4. **Document the change**:
   - Update this document if adding new categories
   - Add migration rules to `scripts/migrate_assets.py`

### Running the Migration

The migration script automates the reorganization:

```bash
# See what would be done without making changes:
python scripts/migrate_assets.py --dry-run

# Execute the migration:
python scripts/migrate_assets.py

# Execute with backward compatibility symlinks:
python scripts/migrate_assets.py --create-symlinks
```

**Note**: Symlinks may not work on all systems (especially Windows without special permissions).

### Migration Log

The script creates a timestamped log file in the project root:
- `migration_log_YYYYMMDD_HHMMSS.txt`

This log contains:
- All directories created
- All files moved
- All path references updated
- Any warnings or errors encountered

## Backward Compatibility

### Symlinks (Optional)

If you run the migration with `--create-symlinks`, the script creates symbolic links from the old paths to the new paths. This allows existing references to continue working without modification.

**Limitations**:
- May not work on Windows without administrator privileges
- Git may not handle symlinks consistently across platforms
- Not recommended for production deployments

### Manual Updates

If you choose not to use symlinks, you'll need to update all references manually. The migration script handles this automatically, but if you're doing it manually, see the "Path Updates" section in `scripts/migrate_assets.py`.

## Best Practices

### Adding New Assets

1. **Place assets in the correct location** based on their type (static vs. generated)
2. **Use descriptive names** that indicate the asset's purpose
3. **Follow naming conventions**:
   - Lowercase with underscores
   - Include type/category in name (e.g., `void_parchment_1.png`)
   - Use sequential numbering for variations

### Referencing Assets

1. **Use relative paths** from the HTML/CSS/JS file's location
2. **CSS**: Use `url('../static/effects/filename.png')` for effects
3. **HTML**: Use `assets/static/elements/type/filename.png` for static assets
4. **HTML**: Use `assets/generated/type/filename.png` for generated assets

### Maintaining the Structure

1. **Don't mix static and generated assets** in the same directory
2. **Keep CSS and JS separate** from image assets
3. **Document new categories** in this file
4. **Update the migration script** when adding new organizational patterns

## Troubleshooting

### Asset Not Found Errors

If you get 404 errors for assets after migration:

1. Check that the file was actually moved to the new location
2. Verify the path in your HTML/CSS matches the new structure
3. If using symlinks, check they were created successfully
4. Clear your browser cache (CSS may be cached)

### Migration Script Failures

If the migration script fails:

1. Check you have write permissions for all directories
2. Ensure no files are open/locked by other processes
3. Review the migration log for specific error details
4. Run with `--dry-run` first to see what would happen

### Reverting the Migration

To revert if something goes wrong:

1. Check the migration log for the original locations
2. Manually move files back to their original locations
3. Restore from git if you committed before migration
4. Revert path updates in modified files

## See Also

- [`scripts/migrate_assets.py`](../scripts/migrate_assets.py) - Migration script with full implementation
- [`generate_assets.py`](../generate_assets.py) - Asset generation logic
- [`backend.py`](../backend.py) - API serving generated assets
- [`docs/design.md`](design.md) - Design system documentation
- [`HANDOFF.md`](../HANDOFF.md) - Project handoff documentation

---

**Last Updated**: 2025-11-24
**Version**: 1.0
**Task**: P2-T2 - Reorganize Asset Directory Structure for Clarity