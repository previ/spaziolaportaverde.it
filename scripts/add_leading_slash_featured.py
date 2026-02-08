#!/usr/bin/env python3
import os, re
root = os.path.join(os.getcwd(), 'content')
pattern = re.compile(r'^(\s*featured_image:\s*)(["\']?)(?!/)(.+?)(["\']?)\s*$', re.IGNORECASE | re.MULTILINE)
files = []
for dirpath, _, filenames in os.walk(root):
    for fn in filenames:
        if not fn.lower().endswith('.md'):
            continue
        path = os.path.join(dirpath, fn)
        with open(path, 'r', encoding='utf-8') as f:
            txt = f.read()
        new, n = pattern.subn(lambda m: f"{m.group(1)}{m.group(2)}/{m.group(3)}{m.group(4)}", txt)
        if n>0:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new)
            files.append(path)
print('Files updated:', len(files))
for p in files:
    print(p)
