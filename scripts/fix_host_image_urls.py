#!/usr/bin/env python3
"""
Fix occurrences of host-prefixed or base-prefixed image URLs and internal links
in the content directory. Replaces:

- http://localhost:1313/spaziolaportaverde.it -> (root-relative) '' (keeps leading slash)
- /spaziolaportaverde.it/images/        -> /images/
- /spaziolaportaverde.it/               -> /

Run from repo root: python3 scripts/fix_host_image_urls.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_DIR = os.path.join(ROOT, 'content')

if not os.path.isdir(TARGET_DIR):
    print('No content/ directory found, exiting')
    sys.exit(1)

replacements = [
    ('http://localhost:1313/spaziolaportaverde.it', ''),
    ('https://localhost:1313/spaziolaportaverde.it', ''),
    ('/spaziolaportaverde.it/images/', '/images/'),
    ('/spaziolaportaverde.it/', '/'),
]

def process_file(path):
    with open(path, 'rb') as f:
        data = f.read()
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        return False

    orig = text
    for a, b in replacements:
        text = text.replace(a, b)

    if text != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        print('Updated', path)
        return True
    return False

count = 0
for root, dirs, files in os.walk(TARGET_DIR):
    for name in files:
        if not name.lower().endswith(('.md', '.html', '.xml', '.txt')):
            continue
        path = os.path.join(root, name)
        try:
            if process_file(path):
                count += 1
        except Exception as e:
            print('Error processing', path, e)

print('Files updated:', count)
