#!/usr/bin/env python3
"""
Asset Directory Migration Script
P2-T2: Reorganize Asset Directory Structure for Clarity

This script migrates the current mixed asset structure to a clear, organized layout
with proper separation between static, generated, CSS, and JS assets.

Usage:
    python scripts/migrate_assets.py [--dry-run] [--create-symlinks]

Options:
    --dry-run          Show what would be done without actually doing it
    --create-symlinks  Create symlinks for backward compatibility (Windows may have issues)
"""

import os
import shutil
import argparse
import sys
from pathlib import Path
from datetime import datetime


class AssetMigrator:
    """Handles migration of asset directory structure"""
    
    def __init__(self, base_dir=".", dry_run=False, create_symlinks=False):
        self.base_dir = Path(base_dir)
        self.dry_run = dry_run
        self.create_symlinks = create_symlinks
        self.log = []
        
        # Define the migration mapping
        self.migration_map = {
            # Static effects (pre-made PNG files)
            "assets/effects/ink_splatter.png": "assets/static/effects/ink_splatter.png",
            "assets/effects/parchment.png": "assets/static/effects/parchment.png",
            "assets/effects/ouroboros.png": "assets/static/effects/ouroboros.png",
            "assets/effects/runes.png": "assets/static/effects/runes.png",
            
            # Static elements (pre-made element images)
            "assets/elements/backgrounds/void_parchment_1.png": "assets/static/elements/backgrounds/void_parchment_1.png",
            "assets/elements/backgrounds/void_parchment_2.png": "assets/static/elements/backgrounds/void_parchment_2.png",
            "assets/elements/backgrounds/void_parchment_3.png": "assets/static/elements/backgrounds/void_parchment_3.png",
            
            "assets/elements/creatures/giraffe_1.png": "assets/static/elements/creatures/giraffe_1.png",
            "assets/elements/creatures/giraffe_2.png": "assets/static/elements/creatures/giraffe_2.png",
            "assets/elements/creatures/giraffe_3.png": "assets/static/elements/creatures/giraffe_3.png",
            "assets/elements/creatures/kangaroo_1.png": "assets/static/elements/creatures/kangaroo_1.png",
            "assets/elements/creatures/kangaroo_2.png": "assets/static/elements/creatures/kangaroo_2.png",
            "assets/elements/creatures/kangaroo_3.png": "assets/static/elements/creatures/kangaroo_3.png",
            
            "assets/elements/glyphs/ink_enso_1.png": "assets/static/elements/glyphs/ink_enso_1.png",
            "assets/elements/glyphs/ink_enso_2.png": "assets/static/elements/glyphs/ink_enso_2.png",
            "assets/elements/glyphs/ink_enso_3.png": "assets/static/elements/glyphs/ink_enso_3.png",
            "assets/elements/glyphs/sigil_1.png": "assets/static/elements/glyphs/sigil_1.png",
            "assets/elements/glyphs/sigil_2.png": "assets/static/elements/glyphs/sigil_2.png",
            "assets/elements/glyphs/sigil_3.png": "assets/static/elements/glyphs/sigil_3.png",
            
            "assets/elements/ui/ink_divider_1.png": "assets/static/elements/ui/ink_divider_1.png",
            "assets/elements/ui/ink_divider_2.png": "assets/static/elements/ui/ink_divider_2.png",
            "assets/elements/ui/ink_divider_3.png": "assets/static/elements/ui/ink_divider_3.png",
            "assets/elements/ui/void_orb_1.png": "assets/static/elements/ui/void_orb_1.png",
            "assets/elements/ui/void_orb_2.png": "assets/static/elements/ui/void_orb_2.png",
            "assets/elements/ui/void_orb_3.png": "assets/static/elements/ui/void_orb_3.png",
            
            # Generated assets (procedurally generated)
            "assets/generated/void_parchment_1.png": "assets/generated/backgrounds/void_parchment_1.png",
            "assets/generated/void_parchment_2.png": "assets/generated/backgrounds/void_parchment_2.png",
            "assets/generated/void_parchment_3.png": "assets/generated/backgrounds/void_parchment_3.png",
            "assets/generated/void_parchment_4.png": "assets/generated/backgrounds/void_parchment_4.png",
            "assets/generated/void_parchment_5.png": "assets/generated/backgrounds/void_parchment_5.png",
            
            "assets/generated/ink_enso_1.png": "assets/generated/glyphs/ink_enso_1.png",
            "assets/generated/ink_enso_2.png": "assets/generated/glyphs/ink_enso_2.png",
            "assets/generated/ink_enso_3.png": "assets/generated/glyphs/ink_enso_3.png",
            "assets/generated/ink_enso_4.png": "assets/generated/glyphs/ink_enso_4.png",
            "assets/generated/ink_enso_5.png": "assets/generated/glyphs/ink_enso_5.png",
            
            "assets/generated/sigil_1.png": "assets/generated/glyphs/sigil_1.png",
            "assets/generated/sigil_2.png": "assets/generated/glyphs/sigil_2.png",
            "assets/generated/sigil_3.png": "assets/generated/glyphs/sigil_3.png",
            "assets/generated/sigil_4.png": "assets/generated/glyphs/sigil_4.png",
            "assets/generated/sigil_5.png": "assets/generated/glyphs/sigil_5.png",
            
            "assets/generated/giraffe_1.png": "assets/generated/creatures/giraffe_1.png",
            "assets/generated/giraffe_2.png": "assets/generated/creatures/giraffe_2.png",
            "assets/generated/giraffe_3.png": "assets/generated/creatures/giraffe_3.png",
            "assets/generated/giraffe_4.png": "assets/generated/creatures/giraffe_4.png",
            "assets/generated/giraffe_5.png": "assets/generated/creatures/giraffe_5.png",
            
            "assets/generated/kangaroo_1.png": "assets/generated/creatures/kangaroo_1.png",
            "assets/generated/kangaroo_2.png": "assets/generated/creatures/kangaroo_2.png",
            "assets/generated/kangaroo_3.png": "assets/generated/creatures/kangaroo_3.png",
            "assets/generated/kangaroo_4.png": "assets/generated/creatures/kangaroo_4.png",
            "assets/generated/kangaroo_5.png": "assets/generated/creatures/kangaroo_5.png",
            
            # CSS and JS stay in place
            "assets/css/unwritten_worlds_common.css": "assets/css/unwritten_worlds_common.css",
            "assets/css/unwritten_worlds.css": "assets/css/unwritten_worlds.css",
            "assets/js/unwritten_worlds_common.js": "assets/js/unwritten_worlds_common.js",
            "assets/js/unwritten_worlds_core.js": "assets/js/unwritten_worlds_core.js",
        }
        
        # Files that need path updates
        self.path_updates = {
            # CSS files
            "assets/css/unwritten_worlds_common.css": [
                (r"url\('\.\./effects/([^']+)'\)", r"url('../static/effects/\1')"),
            ],
            "assets/css/unwritten_worlds.css": [
                (r"url\('\.\./effects/([^']+)'\)", r"url('../static/effects/\1')"),
            ],
            
            # HTML files
            "unwritten_worlds_editor.html": [
                (r"assets/elements/", r"assets/static/elements/"),
            ],
            "unwritten_worlds_effects_library.html": [
                (r"assets/elements/", r"assets/static/elements/"),
            ],
            "unwritten_worlds_loading_examples.html": [
                (r"assets/generated/void_parchment_", r"assets/generated/backgrounds/void_parchment_"),
                (r"assets/generated/ink_enso_", r"assets/generated/glyphs/ink_enso_"),
                (r"assets/generated/sigil_", r"assets/generated/glyphs/sigil_"),
                (r"assets/generated/giraffe_", r"assets/generated/creatures/giraffe_"),
                (r"assets/generated/kangaroo_", r"assets/generated/creatures/kangaroo_"),
            ],
            "enhanced_design/index.html": [
                (r"\.\./assets/", r"../assets/"),  # Already correct, just for reference
            ],
        }
    
    def log_message(self, message, level="INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.log.append(log_entry)
        print(log_entry)
    
    def create_directory(self, dir_path):
        """Create a directory if it doesn't exist"""
        full_path = self.base_dir / dir_path
        
        if not full_path.exists():
            if not self.dry_run:
                full_path.mkdir(parents=True, exist_ok=True)
            self.log_message(f"Created directory: {dir_path}")
            return True
        return False
    
    def move_file(self, source, destination):
        """Move a file from source to destination"""
        source_path = self.base_dir / source
        dest_path = self.base_dir / destination
        
        if not source_path.exists():
            self.log_message(f"Source file not found: {source}", "WARNING")
            return False
        
        # Create destination directory
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.dry_run:
            shutil.move(str(source_path), str(dest_path))
        
        self.log_message(f"Moved: {source} -> {destination}")
        return True
    
    def create_symlink(self, target, link_name):
        """Create a symlink for backward compatibility"""
        if not self.create_symlinks:
            return
        
        target_path = self.base_dir / target
        link_path = self.base_dir / link_name
        
        if target_path.exists() and not link_path.exists():
            if not self.dry_run:
                try:
                    os.symlink(target_path, link_path)
                    self.log_message(f"Created symlink: {link_name} -> {target}")
                except OSError as e:
                    self.log_message(f"Failed to create symlink {link_name}: {e}", "ERROR")
            else:
                self.log_message(f"Would create symlink: {link_name} -> {target}")
    
    def update_file_paths(self, file_path, patterns):
        """Update paths in a file using regex patterns"""
        file_full_path = self.base_dir / file_path
        
        if not file_full_path.exists():
            self.log_message(f"File not found for path update: {file_path}", "WARNING")
            return False
        
        with open(file_full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        for pattern, replacement in patterns:
            import re
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            if not self.dry_run:
                with open(file_full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            self.log_message(f"Updated paths in: {file_path}")
            return True
        
        return False
    
    def run_migration(self):
        """Execute the full migration"""
        self.log_message("=" * 60)
        self.log_message("Starting Asset Directory Migration")
        self.log_message("=" * 60)
        
        if self.dry_run:
            self.log_message("DRY RUN MODE - No files will be modified")
        
        # Create new directory structure
        self.log_message("\nCreating new directory structure...")
        directories = [
            "assets/static/effects",
            "assets/static/elements/backgrounds",
            "assets/static/elements/creatures",
            "assets/static/elements/glyphs",
            "assets/static/elements/ui",
            "assets/generated/backgrounds",
            "assets/generated/creatures",
            "assets/generated/glyphs",
            "assets/generated/ui",
            "assets/css",
            "assets/js",
        ]
        
        for directory in directories:
            self.create_directory(directory)
        
        # Move files to new locations
        self.log_message("\nMoving files to new structure...")
        moved_count = 0
        for source, destination in self.migration_map.items():
            if source != destination:  # Skip files that stay in place
                if self.move_file(source, destination):
                    moved_count += 1
                    
                    # Create symlink for backward compatibility
                    if self.create_symlinks:
                        self.create_symlink(destination, source)
        
        # Update path references in files
        self.log_message("\nUpdating path references...")
        updated_count = 0
        for file_path, patterns in self.path_updates.items():
            if self.update_file_paths(file_path, patterns):
                updated_count += 1
        
        # Summary
        self.log_message("\n" + "=" * 60)
        self.log_message("Migration Summary")
        self.log_message("=" * 60)
        self.log_message(f"Files moved: {moved_count}")
        self.log_message(f"Files updated: {updated_count}")
        
        if self.dry_run:
            self.log_message("\nThis was a DRY RUN. No files were modified.")
            self.log_message("Run without --dry-run to execute the migration.")
        
        if self.create_symlinks:
            self.log_message("\nSymlinks created for backward compatibility.")
            self.log_message("Note: Symlinks may not work on all systems (especially Windows).")
        
        self.log_message("\nMigration complete!")
        
        # Save log to file
        log_file = self.base_dir / f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        if not self.dry_run:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.log))
            self.log_message(f"\nLog saved to: {log_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate asset directory structure for clarity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # See what would be done without making changes:
  python scripts/migrate_assets.py --dry-run
  
  # Execute the migration:
  python scripts/migrate_assets.py
  
  # Execute with backward compatibility symlinks:
  python scripts/migrate_assets.py --create-symlinks
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually doing it'
    )
    
    parser.add_argument(
        '--create-symlinks',
        action='store_true',
        help='Create symlinks for backward compatibility (may not work on Windows)'
    )
    
    parser.add_argument(
        '--base-dir',
        default='.',
        help='Base directory to work from (default: current directory)'
    )
    
    args = parser.parse_args()
    
    migrator = AssetMigrator(
        base_dir=args.base_dir,
        dry_run=args.dry_run,
        create_symlinks=args.create_symlinks
    )
    
    try:
        migrator.run_migration()
        return 0
    except Exception as e:
        print(f"\n❌ Migration failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())