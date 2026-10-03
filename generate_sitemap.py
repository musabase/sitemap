import json
import urllib.request
from datetime import datetime, timezone

POSTS_FEED = "https://www.musabase.com/feeds/posts/default?alt=json&max-results=500"
PAGES_FEED = "https://www.musabase.com/feeds/pages/default?alt=json&max-results=500"

def fetch_entries(feed_url, label):
    req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode("utf-8"))
    entries = data.get("feed", {}).get("entry", [])
    print(f"[{label}] Raw entries returned by feed: {len(entries)}")
    return entries

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
    return xml

if __name__ == "__main__":
    posts = fetch_entries(POSTS_FEED, "posts")
    pages = fetch_entries(PAGES_FEED, "pages")
    all_entries = posts + pages
    sitemap_xml = build_sitemap(all_entries)
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap_xml)
    print(f"\nGenerated sitemap with {len(urls_in := sitemap_xml.count('<url>'))} entries ({len(posts)} raw posts, {len(pages)} raw pages)")
