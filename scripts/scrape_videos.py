#!/usr/bin/env python3
import os
import re
import sys
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser
from urllib.request import urlopen, Request

# Configuration
ROOTS = [
    'http://www.spaziolaportaverde.it',
    'https://www.spaziolaportaverde.it',
]
OUT_HTML = os.path.join(os.path.dirname(__file__), '..', 'static', '_scraped_html')
OUTDIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'videos')
os.makedirs(OUT_HTML, exist_ok=True)
os.makedirs(OUTDIR, exist_ok=True)


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        for k, v in attrs:
            if not v:
                continue
            if k.lower() in ('href', 'src', 'data-src'):
                self.links.append(v)


def same_domain(url):
    p = urlparse(url)
    return p.netloc.endswith('spaziolaportaverde.it') or p.netloc == ''


def fetch(url):
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=20) as r:
            data = r.read()
            try:
                return data.decode('utf-8')
            except Exception:
                return data.decode('latin-1', errors='ignore')
    except Exception:
        return ''


def save_html(url, html):
    parsed = urlparse(url)
    path = parsed.path or '/'
    if path.endswith('/'):
        path = path + 'index.html'
    dest_dir = os.path.join(OUT_HTML, parsed.netloc, os.path.dirname(path.lstrip('/')))
    os.makedirs(dest_dir, exist_ok=True)
    fname = os.path.join(dest_dir, os.path.basename(path))
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(html)
    return fname


def download_file(url):
    try:
        parsed = urlparse(url)
        fname = os.path.basename(parsed.path)
        if not fname:
            return False
        dest = os.path.join(OUTDIR, fname)
        if os.path.exists(dest):
            return False
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=60) as r, open(dest, 'wb') as out:
            out.write(r.read())
        return True
    except Exception:
        return False


def crawl(starts=ROOTS, max_depth=3):
    seen = set()
    to_visit = [(s, 0) for s in starts]
    while to_visit:
        url, depth = to_visit.pop(0)
        if url in seen or depth > max_depth:
            continue
        seen.add(url)
        print('Crawling', url)
        html = fetch(url)
        if not html:
            continue
        try:
            save_html(url, html)
        except Exception:
            pass
        parser = LinkParser()
        try:
            parser.feed(html)
        except Exception:
            # tolerate malformed HTML from legacy pages
            continue
        for link in parser.links:
            try:
                raw = link.strip()
                if not raw:
                    continue
                full = urljoin(url, raw)
                # quote spaces and other unsafe chars in path
                full = full.replace(' ', '%20')
            except Exception:
                continue
            # follow any http(s) link on same domain (be liberal)
            parsed_full = urlparse(full)
            if parsed_full.scheme not in ('http', 'https'):
                continue
            if not same_domain(full):
                continue
            if full in seen:
                continue
            to_visit.append((full, depth + 1))


def scan_saved_html_and_download():
    http_media = re.compile(r'https?://[^\s"\']+\.(?:mp4|webm|ogg|m3u8)', re.IGNORECASE)
    src_href = re.compile(r'(?:src|href)\s*=\s*(["\'])([^"\']+)\1', re.IGNORECASE)
    downloaded = []
    for root, _, files in os.walk(OUT_HTML):
        for fn in files:
            if not fn.lower().endswith('.html'):
                continue
            path = os.path.join(root, fn)
            try:
                text = open(path, 'r', encoding='utf-8', errors='ignore').read()
            except Exception:
                continue
            # absolute http(s) media links
            for m in http_media.finditer(text):
                full = m.group(0)
                if same_domain(full) and download_file(full):
                    downloaded.append(full)
            # src/href links (may be relative)
            for m in src_href.finditer(text):
                link = m.group(2)
                if any(link.lower().endswith(ext) for ext in ('.mp4', '.webm', '.ogg', '.m3u8')):
                    # find netloc directory from saved path
                    parts = path.split(os.sep)
                    netloc = None
                    for i, part in enumerate(parts):
                        if part.endswith('spaziolaportaverde.it'):
                            netloc = part
                            base_url = 'http://' + netloc + '/'
                            break
                    if not netloc:
                        base_url = 'http://www.spaziolaportaverde.it/'
                    full = urljoin(base_url, link)
                    if same_domain(full) and download_file(full):
                        downloaded.append(full)
    return downloaded


def main():
    print('Starting crawl (saving HTML)...')
    max_depth = 3
    if len(sys.argv) > 1:
        try:
            max_depth = int(sys.argv[1])
        except Exception:
            pass
    crawl(max_depth=max_depth)
    print(f'\nCrawl complete (depth={max_depth}). Scanning saved HTML for media links...')
    vids = scan_saved_html_and_download()
    if vids:
        print('\nDownloaded media:')
        for v in vids:
            print(v)
    else:
        print('No media downloaded')


if __name__ == '__main__':
    main()
