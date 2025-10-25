# fetch_sitemap.py
import os
from lxml import etree

MAIN_SITEMAP = "GoogleSitemap.xml"
OUTPUT_FILE = "shufersal_products.txt"

def parse_sitemap_file(file_path):
    """Return all <loc> URLs from a sitemap XML file."""
    with open(file_path, "r", encoding="utf-8") as f:
        xml_text = f.read()

    root = etree.fromstring(xml_text.encode("utf-8"))
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = root.xpath("//sm:loc/text()", namespaces=ns)
    return locs

def main():
    if not os.path.exists(MAIN_SITEMAP):
        print(f"❌ Main sitemap not found: {MAIN_SITEMAP}")
        return

    print(f"📂 Reading main sitemap: {MAIN_SITEMAP}")
    urls = parse_sitemap_file(MAIN_SITEMAP)
    print(f"Found {len(urls)} URLs in main sitemap.")

    # Filter to find linked sub-sitemaps (they usually end with .xml)
    sub_sitemaps = [u for u in urls if u.lower().endswith(".xml")]
    print(f"🔗 Found {len(sub_sitemaps)} sub-sitemaps.")

    all_products = []

    # Iterate through each sub-sitemap file if downloaded locally
    for sub in sub_sitemaps:
        filename = os.path.basename(sub)
        if not os.path.exists(filename):
            print(f"⚠️  Missing local file for {filename}. Please download it.")
            continue
        print(f"📦 Parsing {filename} …")
        sub_urls = parse_sitemap_file(filename)
        product_urls = [u for u in sub_urls if "/product/" in u or "/p/" in u]
        print(f"   🛒 {len(product_urls)} product URLs found.")
        all_products.extend(product_urls)

    # Save all collected product URLs
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for u in all_products:
            f
