import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

BASE_URL = "http://www.spaziolaportaverde.it/"
CONTENT_DIR = "content"
STATIC_DIR = "static/images"

ENTRY_POINTS = [
    "http://www.spaziolaportaverde.it/",
    "http://www.spaziolaportaverde.it/htm/Spazio%20La%20Porta%20Verde/le%20mostre.htm",
    "http://www.spaziolaportaverde.it/htm/Gabriella%20Ventavoli/Gabriella%20Ventavoli.html",
    "http://www.spaziolaportaverde.it/htm/Gabriella%20Ventavoli/Libri.html"
]

scanned_urls = set()
url_to_slug = {}

def slugify(url):
    path = urlparse(url).path
    name = os.path.basename(path).split('.')[0]
    if not name or name == 'index' or name == 'default':
        name = os.path.basename(os.path.dirname(path))
    name = name.lower().replace('%20', '-').replace(' ', '-')
    name = re.sub(r'[^a-z0-9-]+', '', name)
    return name.strip('-')

def get_content_safe(url):
    try:
        response = requests.get(url, timeout=15)
        # Force windows-1252 as it's common for legacy Italian sites and was verified by browser
        response.encoding = 'windows-1252'
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def clean_html(soup):
    for script in soup(["script", "style"]):
        script.extract()
    
    # Remove redundant title "SPAZIO LA PORTA VERDE"
    for p in soup.find_all('p'):
        if "SPAZIO LA PORTA VERDE" in p.get_text():
            p.decompose()

    for a in soup.find_all(['a', 'button']):
        text = a.get_text().lower()
        if any(word in text for word in ['chiudi', 'torna', 'home', 'back', 'close']):
            a.decompose()
    return soup

def download_image(img_url, page_url):
    full_url = urljoin(page_url, img_url)
    filename = os.path.basename(urlparse(full_url).path)
    if not filename: return img_url
    filename = re.sub(r'[^a-zA-Z0-9\._-]', '_', filename)
    local_path = os.path.join(STATIC_DIR, filename)
    if not os.path.exists(local_path):
        try:
            r = requests.get(full_url, stream=True, timeout=10)
            if r.status_code == 200:
                with open(local_path, 'wb') as f:
                    for chunk in r.iter_content(1024): f.write(chunk)
        except: pass
    return f"/images/{filename}"

def force_entities(text):
    # Only encode non-ASCII that aren't already entities
    return "".join(f"&#{ord(c)};" if ord(c) > 127 else c for c in text)

def extract_date(text):
    # Try to find a year in the text (1990-2029)
    match = re.search(r'\b(19|20)\d{2}\b', text)
    if match:
        return f"{match.group(0)}-01-01"
    return "2000-01-01" # Default old date

if __name__ == "__main__":
    os.makedirs(STATIC_DIR, exist_ok=True)
    
    queue = ENTRY_POINTS.copy()
    processed_data = []
    
    # Increased limit to catch all pages
    while queue and len(scanned_urls) < 200:
        url = queue.pop(0)
        if url in scanned_urls: continue
        scanned_urls.add(url)
        
        text = get_content_safe(url)
        if not text: continue
        
        slug = slugify(url)
        if not slug: slug = "home"
        
        # Avoid overriding important slugs
        if slug in [d["slug"] for d in processed_data]:
            slug = f"{slug}-{len(processed_data)}"
            
        url_to_slug[url] = slug
        soup = BeautifulSoup(text, 'html.parser')
        title = soup.title.string if soup.title and soup.title.string else slug.capitalize()
        
        # Extract date from title and content
        date_source = f"{title} {soup.get_text()}"
        page_date = extract_date(date_source)

        # Discovery
        for a in soup.find_all('a', href=True):
            href = a['href']
            if any(href.startswith(p) for p in ['mailto:', 'tel:', 'javascript:', '#']):
                continue
            
            full_href = urljoin(url, href)
            parsed = urlparse(full_href)
            if parsed.netloc == urlparse(BASE_URL).netloc:
                if parsed.path.lower().endswith(('.htm', '.html', '.php')) or parsed.path == '/' or parsed.path == '':
                    clean_url = full_href.split('#')[0]
                    if clean_url not in scanned_urls:
                        queue.append(clean_url)
        
        soup = clean_html(soup)
        featured_image = ""
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                local_src = download_image(src, url)
                img['src'] = local_src
                if not featured_image:
                    featured_image = local_src
            
        processed_data.append({
            "url": url, 
            "slug": slug, 
            "soup": soup, 
            "title": title,
            "featured_image": featured_image,
            "page_date": page_date
        })
        print(f"Processed: {url} -> {slug}")

    # Link rewriting
    for data in processed_data:
        soup = data["soup"]
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '@' in href and not any(href.startswith(p) for p in ['mailto:', 'http']):
                a['href'] = f"mailto:{href}"
                continue
                
            full_href = urljoin(data["url"], href)
            clean_url = full_href.split('#')[0]
            if clean_url in url_to_slug:
                a['href'] = f"/{url_to_slug[clean_url]}/"
        
        if "Intervista" in title:
            content_type = "Intervista"
        elif "Mostra" in title:
            content_type = "Mostra"
        elif any(x in str(soup) for x in ["iframe", "youtube", "vimeo"]):
            content_type = "Video"
            # Always force the placeholder for videos, ignoring scraped images
            featured_image = "/images/video-placeholder.jpg"
        else:
            content_type = "Mostra" # Default

        # Use extracted date for sorting
        page_date = data["page_date"]
        md_content = f'---\ntitle: "{data["title"].strip()}"\ndate: {page_date}\ndraft: false\nfeatured_image: "{featured_image}"\ntype_label: "{content_type}"\n---\n\n{content_html}\n'
        
        # Determine target path
        target_dir = CONTENT_DIR
        slug = data["slug"]
        if slug in ['finalita', 'lo-spazio', 'biografia', 'contatti']:
            target_dir = os.path.join(CONTENT_DIR, 'centro')
        elif slug in ['libri', 'novita']:
            target_dir = os.path.join(CONTENT_DIR, 'attivita')
        elif slug != 'home':
            target_dir = os.path.join(CONTENT_DIR, 'attivita', 'mostre')
            
        os.makedirs(target_dir, exist_ok=True)
        filename = f"{slug}.md"
        with open(os.path.join(target_dir, filename), "w", encoding='utf-8') as f:
            f.write(md_content)

    print("Migration complete!")
