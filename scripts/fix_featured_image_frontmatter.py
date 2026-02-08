#!/usr/bin/env python3
import os
import re

root = os.path.join(os.getcwd(), 'content')
if not os.path.isdir(root):
    print('content/ directory not found; run from repo root')
    raise SystemExit(1)

pattern = re.compile(r'^(\s*featured_image:\s*)(["\']?)(/)(.+?)(["\']?)\s*$', re.IGNORECASE | re.MULTILINE)
files_updated = []
total_replacements = 0

for dirpath, _, filenames in os.walk(root):
    for name in filenames:
        if not name.lower().endswith('.md'):
            continue
        path = os.path.join(dirpath, name)
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()

        def repl(m):
            nonlocal_match = m
            # keep same quoting if present
            quote_start = m.group(2) or ''
            quote_end = m.group(5) or ''
            new = f"{m.group(1)}{quote_start}{m.group(4)}{quote_end}"
            return new

        newtext, n = pattern.subn(repl, text)
        if n > 0:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(newtext)
            files_updated.append(path)
            total_replacements += n

print(f"Files updated: {len(files_updated)}")
for p in files_updated:
    print(p)
print(f"Total replacements: {total_replacements}")
