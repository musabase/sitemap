import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

def fetch_xml(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response:
        return ET.fromstring(response.read())

def collect_urls(sitemap_url, collected):
    root = fetch_xml(sitemap_url)
    tag = root.tag

    if tag == f"{NS}sitemapindex":
        print(f"'{sitemap_url}' is an index, following sub-sitemaps...")
        for sitemap in root.findall(f"{NS}sitemap"):
            loc = sitemap.find(f"{NS}loc").text
            collect_urls(loc, collected)
    elif tag == f"{NS}urlset":
        entries = root.findall(f"{NS}url")
        print(f"'{sitemap_url}' contains {len(entries)} URLs")
        for url_entry in entries:
            loc = url_entry.find(f"{NS}loc").text
            lastmod_el = url_entry.find(f"{NS}lastmod")
            lastmod = lastmod_el.text if lastmod_el is not None else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            collected[loc] = lastmod
    else:
        print(f"⚠️ Unexpected root tag in '{sitemap_url}': {tag}")

if __name__ == "__main__":
    collected = {}
    collect_urls("https://www.musabase.com/sitemap.xml", collected)
    collect_urls("https://www.musabase.com/sitemap-pages.xml", collected)

    urls_xml = "\n".join(
        f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod></url>"
        for loc, lastmod in collected.items()
    )

    sitemap_xml = (
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + urls_xml
        + "\n</urlset>\n"
    )

    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap_xml)

    print(f"\nGenerated sitemap with {len(collected)} total URLs")
