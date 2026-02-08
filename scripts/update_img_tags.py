#!/usr/bin/env python3
"""Convert HTML <img src="/images/..."> in content files to Hugo shortcode usage.

This script looks for <img ...> tags where the src begins with /images/
and replaces them with: {{< img src="images/path.jpg" alt="..." class="..." >}}

Run from site root: python3 scripts/update_img_tags.py
"""
import re
from pathlib import Path

IMG_RE = re.compile(r'<img\s+([^>]*?)src=(?P<q>["\'])(/images/(?P<src>[^"\']+))(?P=q)([^>]*)>', re.IGNORECASE)

def attrs_from_match(g1, g5):
    # g1 is attributes before src, g5 is attributes after src
    attrs = (g1 + ' ' + g5).strip()
    # simple attr parser: find key="value" or key='value'
    pairs = re.findall(r"(\w+)=(\"[^\"]*\"|'[^']*')", attrs)
    d = {}
    for k,v in pairs:
        # strip surrounding quotes
        if v.startswith('"') and v.endswith('"'):
            val = v[1:-1]
        elif v.startswith("'") and v.endswith("'"):
            val = v[1:-1]
        else:
            val = v
        d[k.lower()] = val
    return d

def make_shortcode(src, attrs):
    # remove leading slash from src if present
    src = src.lstrip('/')
    # ensure path includes images/ prefix
    if not src.startswith('images/'):
        src = 'images/' + src
    parts = [f'src="{src}"']
    for k in ('alt','class','width','height','title'):
        if k in attrs:
            parts.append(f'{k}="{attrs[k]}"')
    return '{{< img ' + ' '.join(parts) + ' >}}'

def process_file(path: Path):
    text = path.read_text(encoding='utf-8')
    # group 3 is the full /images/... and group 5 is attributes after src
    new, count = IMG_RE.subn(lambda m: make_shortcode(m.group(3), attrs_from_match(m.group(1), m.group(5))), text)
    if count:
        path.write_text(new, encoding='utf-8')
        print(f'Updated {count} image(s) in {path}')

def main():
    root = Path('content')
    if not root.exists():
        print('content/ not found; aborting')
        return
    files = list(root.rglob('*.md')) + list(root.rglob('*.html'))
    for f in files:
        process_file(f)

if __name__ == '__main__':
    main()
