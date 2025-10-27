import json, time
from playwright.sync_api import sync_playwright

CATEGORY_URL = "https://www.shufersal.co.il/online/he/קטגוריות/סופרמרקט/חלב-וביצים/c/A01"
OUTPUT_FILE = "shufersal_final_modal.json"
PRODUCT_LIMIT = 10
DELAY_SECONDS = 5


def extract_full_modal_data(page):
    modal = page.locator("#productModal")
    modal.wait_for(timeout=12000)
    time.sleep(0.8)

    data = {}

    # ✅ Correct popup title
    try:
        data["שם המוצר"] = modal.locator("h2#modalTitle.title.description").inner_text().strip()
    except:
        try:
            data["שם המוצר"] = modal.locator("h1, .modal-title").first.inner_text().strip()
        except:
            data["שם המוצר"] = ""

    # --- Price ---
    try:
        data["מחיר"] = modal.locator(".number").first.inner_text().strip()
        data["מחיר ליחידה"] = modal.locator(".smallText:has-text('ש\"ח')").first.inner_text().strip()
    except:
        pass

    # --- Brand / Size line ---
    try:
        data["מותג"] = modal.locator(".brand-name").first.inner_text().strip()
    except:
        pass

    # --- Image ---
    try:
        img = modal.locator("img.pic, img[itemprop='image']").first.get_attribute("src")
        if img:
            data["תמונה"] = img
    except:
        pass

    # --- Nutrition ---
    nutrition = {}
    for item in modal.locator(".nutritionItem").all():
        try:
            key = item.locator(".text").inner_text().strip()
            val = item.locator(".number").inner_text().strip()
            if key and val:
                nutrition[key] = val
        except:
            pass
    if nutrition:
        data["ערכים תזונתיים"] = nutrition

    # --- Preview text ---
    try:
        text = modal.inner_text()
        data["raw_preview"] = text[:300]
    except:
        pass

    return data


def main():
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=150)
        context = browser.new_context()
        page = context.new_page()

        print(f"⚙️ Opening category: {CATEGORY_URL}")
        page.goto(CATEGORY_URL, timeout=60000)
        page.wait_for_timeout(3000)
        print("✅ Category page loaded")

        # Scroll to load all cards
        for _ in range(6):
            page.mouse.wheel(0, 1500)
            time.sleep(0.5)

        cards = page.locator("li.miglog-prod")
        total = cards.count()
        print(f"🧱 Found {total} product cards")
        limit = min(total, PRODUCT_LIMIT)

        for i in range(limit):
            print(f"\n[{i+1}/{limit}] Opening modal…")
            card = cards.nth(i)
            try:
                link = card.locator("a.imgContainer[data-target='#productModal']").first
                link.scroll_into_view_if_needed()
                link.click(force=True)
                page.wait_for_selector("#productModal.show, #productModal.in", timeout=10000)

                product = extract_full_modal_data(page)
                print(f"   ✅ {product.get('שם המוצר', 'No title')}")
                results.append(product)

                # Close modal
                if page.locator("#productModal button.close").count():
                    page.locator("#productModal button.close").click(force=True)
                else:
                    page.keyboard.press("Escape")
                page.wait_for_timeout(800)

            except Exception as e:
                print(f"   ⚠️ Error: {e}")
                page.keyboard.press("Escape")
                page.wait_for_timeout(800)

            time.sleep(DELAY_SECONDS)

        browser.close()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved {len(results)} products → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
