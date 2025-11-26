#!/usr/bin/env python3
# Convert all single-line triple-quote docstrings to comments in backend.py

import re

with open('backend.py', 'r', encoding='latin-1') as f:
    content = f.read()

# Pattern to match single-line docstrings like:     """Some text."""
# This regex finds indented triple-quote strings on a single line
pattern = r'^(\s+)"""(.+?)"""$'

def replace_docstring(match):
    indent = match.group(1)
    text = match.group(2).strip()
    return f"{indent}# {text}"

# Replace all occurrences
fixed_content = re.sub(pattern, replace_docstring, content, flags=re.MULTILINE)

# Write back
with open('backend.py', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

# Count how many were replaced
count = len(re.findall(pattern, content, re.MULTILINE))
print(f"Converted {count} single-line docstrings to comments")
