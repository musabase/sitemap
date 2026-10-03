import json
import urllib.request
from datetime import datetime, timezone

def fetch_all_entries(feed_base_url, label, page_size=100):
    all_entries = []
    start_index = 1
    while True:
        url = f"{feed_base_url}?alt=json&max-results={page_size}&start-index={start_index}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
        batch = data.get("feed", {}).get("entry", [])
        print(f"[{label}] Fetched {len(batch)} entries starting at index {start_index}")
        if not batch:
            break
        all_entries.extend(batch)
        if len(batch) < page_size:
            break
        start_index += page_size
    print(f"[{label}] Total entries collected: {len(all_entries)}")
    return all_entries

def extract_url(entry):
    for link in entry.get("link", []):
        if link.get("rel") == "alternate":
            return link.get("href")
    return None

def extract_title(entry):
    return entry.get("title", {}).get("$t", "UNKNOWN TITLE")

def extract_lastmod(entry):
    updated = entry.get("updated", {}).get("$t")
    if updated:
        dt = datetime.fromisoformat(updated)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def build_sitemap(entries):
    urls = []
    seen = set()
    skipped = []
    for entry in entries:
        url = extract_url(entry)
        title = extract_title(entry)
        if not url:
            skipped.append((title, "no alternate link found"))
            continue
        if "/search" in url:
            skipped.append((title, f"filtered (search URL): {url}"))
            continue
        if url in seen:
            skipped.append((title, f"duplicate: {url}"))
            continue
        seen.add(url)
        lastmod = extract_lastmod(entry)
        urls.append(f"  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod></url>")

    if skipped:
        print(f"\n⚠️  Skipped {len(skipped)} entries:")
        for title, reason in skipped:
            print(f"  - \"{title}\": {reason}")

    xml = (
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    return xml, len(urls)

if __name__ == "__main__":
    posts = fetch_all_entries("https://www.musabase.com/feeds/posts/default", "posts")
    pages = fetch_all_entries("https://www.musabase.com/feeds/pages/default", "pages")
    all_entries = posts + pages
    sitemap_xml, url_count = build_sitemap(all_entries)
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap_xml)
    print(f"\nGenerated sitemap with {url_count} URLs ({len(posts)} raw posts, {len(pages)} raw pages)")
