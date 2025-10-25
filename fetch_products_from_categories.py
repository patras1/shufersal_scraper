import json, time
from playwright.sync_api import sync_playwright

CATEGORY_URL = "https://www.shufersal.co.il/online/he/קטגוריות/סופרמרקט/חלב-וביצים/c/A01"
OUTPUT_FILE = "shufersal_full_modal_title_h2_fixed.json"
PRODUCT_LIMIT = 10
DELAY_SECONDS = 2
SCROLL_ROUNDS = 4


def extract_full_modal_data(page):
    modal = page.locator("#productModal")
    modal.wait_for(timeout=8000)
    page.wait_for_timeout(500)

    # Scroll inside modal to make sure all content loads
    scroll_area = modal.locator(".productContainer, .bottom-sheet-modal-container")
    for _ in range(SCROLL_ROUNDS):
        try:
            scroll_area.evaluate("(el) => el.scrollBy(0, 1000)")
        except:
            pass
        page.wait_for_timeout(150)

    text = modal.inner_text()
    data = {}

    # --- ✅ Correct product title (from <h2 id="modalTitle" class="title description">) ---
    try:
        data["שם המוצר"] = modal.locator("h2#modalTitle.title.description").first.inner_text().strip()
    except:
        try:
            data["שם המוצר"] = modal.locator("#productModal h2.title.description, h1, .modal-title").first.inner_text().strip()
        except:
            data["שם המוצר"] = ""

    # --- Price ---
    try:
        data["מחיר"] = modal.locator(".number").first.inner_text().strip()
        data["מחיר ליחידה"] = modal.locator(".smallText:has-text('ש\"ח')").first.inner_text().strip()
    except:
        pass

    # --- Brand / Quantity ---
    try:
        data["מותג"] = modal.locator(".brand-name").first.inner_text().strip()
    except:
        pass

    # --- Image URL ---
    try:
        img = modal.locator("img.pic, img[itemprop='image']").first.get_attribute("src")
        if img:
            data["תמונה"] = img
    except:
        pass

    # --- Ingredients ---
    try:
        for line in text.splitlines():
            if "רכיבים" in line and len(line) < 200:
                data["רכיבים"] = line.replace("רכיבים", "").strip()
                break
    except:
        pass

    # --- Nutrition values ---
    nutrition = {}
    for it in modal.locator(".nutritionItem").all():
        try:
            key = it.locator(".text").inner_text().strip()
            val = it.locator(".number").inner_text().strip()
            if key and val:
                nutrition[key] = val
        except:
            pass
    if nutrition:
        data["ערכים תזונתיים"] = nutrition

    data["raw_preview"] = text[:300]
    return data


def main():
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=80)
        context = browser.new_context()
        page = context.new_page()

        print(f"⚙️ Opening category: {CATEGORY_URL}")
        page.goto(CATEGORY_URL, timeout=60000)
        page.wait_for_timeout(2500)
        print("✅ Category page loaded")

        # Scroll to load all visible items
        for _ in range(4):
            page.mouse.wheel(0, 1500)
            time.sleep(0.3)

        cards = page.locator("li.miglog-prod a.imgContainer[data-target='#productModal']")
        total = cards.count()
        print(f"🧱 Found {total} products")

        for i in range(min(total, PRODUCT_LIMIT)):
            print(f"\n[{i+1}/{PRODUCT_LIMIT}] Opening modal…")
            try:
                card = cards.nth(i)
                card.scroll_into_view_if_needed()
                card.click(force=True)
                page.wait_for_selector("#productModal", timeout=8000)

                product = extract_full_modal_data(page)
                print(f"   ✅ Extracted: {product.get('שם המוצר') or '—'}")
                results.append(product)

                # Close modal
                if page.locator("#productModal button.close").count():
                    page.locator("#productModal button.close").click(force=True)
                else:
                    page.keyboard.press("Escape")
                page.wait_for_timeout(400)

            except Exception as e:
                print("   ⚠️ Error:", e)
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)

            print(f"⏳ Wait {DELAY_SECONDS}s…")
            time.sleep(DELAY_SECONDS)

        browser.close()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Saved {len(results)} full products → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
