#!/usr/bin/env python3
import re
import glob
import os

def has_featured(frontmatter):
    m = re.search(r"(?m)^featured_image\s*:\s*['\"]?(.*?)['\"]?\s*$", frontmatter)
    if m:
        v = m.group(1).strip()
        return len(v) > 0
    return False

html_img_re = re.compile(r'(?i)<img[^>]+src=["\']([^"\']+)["\']')
shortcode_img_re = re.compile(r'{{<\s*img[^>]*src=["\']([^"\']+)["\'][^>]*>}}')
md_img_re = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')

video_hosts = ("youtube.com", "youtu.be", "vimeo.com")

files = sorted(glob.glob('content/attivita/mostre/*.md'))
missing = []
for path in files:
    with open(path, 'r', encoding='utf-8') as f:
        txt = f.read()
    # split frontmatter
    front = ''
    body = txt
    if txt.startswith('---'):
        parts = txt.split('---', 2)
        if len(parts) >= 3:
            front = parts[1]
            body = parts[2]
    ok = False
    if has_featured(front):
        ok = True
    else:
        # search shortcode
        if shortcode_img_re.search(txt):
            ok = True
        elif html_img_re.search(body):
            # ensure not only video iframe
            for m in html_img_re.finditer(body):
                src = m.group(1)
                if any(h in src for h in video_hosts):
                    continue
                ok = True
                break
        elif md_img_re.search(body):
            for m in md_img_re.finditer(body):
                src = m.group(1)
                if any(h in src for h in video_hosts):
                    continue
                ok = True
                break
    if not ok:
        missing.append(path)

print(f"Checked {len(files)} files in content/attivita/mostre")
print(f"Files missing thumbnails: {len(missing)}")
for p in missing:
    print(p)
