#!/usr/bin/env python3
# Clean and re-encode backend.py

# Read with Latin-1 (which accepts all byte values)
with open('backend.py', 'r', encoding='latin-1') as f:
    content = f.read()

# Write back as UTF-8, replacing problematic characters
with open('backend.py', 'w', encoding='utf-8', errors='replace') as f:
    f.write(content)

print(f"Re-encoded file. Length: {len(content)} characters")
