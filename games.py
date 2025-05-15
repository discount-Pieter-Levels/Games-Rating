import gspread
from google.oauth2.service_account import Credentials
from playwright.sync_api import sync_playwright
import urllib.parse
import time

# 🔐 Setup Google Sheets API
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
client = gspread.authorize(creds)

# 📄 Open your sheet
sheet_id = "1Psb0ED5yH5hJ3GN70ooPIp74ReGy8Xk7W5nHLLIF93M"
worksheet = client.open_by_key(sheet_id).sheet1

# ➕ Add "OpenCritic Rating" column if not exists
header = worksheet.row_values(1)
if "OpenCritic Rating" not in header:
    worksheet.update_cell(1, len(header) + 1, "OpenCritic Rating")
    rating_col = len(header) + 1
else:
    rating_col = header.index("OpenCritic Rating") + 1

# 🔍 Scrape OpenCritic Top Critic Average using Playwright
def get_opencritic_rating(game_title):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # 1. Search
            search_url = f"https://opencritic.com/search/all/{urllib.parse.quote(game_title)}"
            page.goto(search_url, timeout=60000)
            page.wait_for_timeout(2000)

            # 2. Check for results
            if page.locator(".searchResultTitle").count() == 0:
                print(f"⚠️ No results found for '{game_title}' on OpenCritic.")
                browser.close()
                return None

            # 3. Click the first result
            page.locator(".searchResultTitle").first.click()
            page.wait_for_timeout(2000)

            # 4. Try to get Top Critic Average
            if page.locator(".gauge-meter__value").count() > 0:
                rating = page.locator(".gauge-meter__value").first.inner_text().strip()
                browser.close()
                return rating
            else:
                print(f"⚠️ No Top Critic Average for '{game_title}'.")
                browser.close()
                return "N/A"

    except Exception as e:
        print(f"❌ Error fetching OpenCritic rating for '{game_title}': {e}")
        return None


# 🌀 Loop through games and update
titles = worksheet.col_values(header.index("Title") + 1)

for i in range(1, len(titles)):
    title = titles[i]
    print(f"🔍 Checking OpenCritic for: {title}")
    rating = get_opencritic_rating(title)

    if rating:
        worksheet.update_cell(i + 1, rating_col, rating)
        print(f"✅ {title}: {rating}")
    else:
        worksheet.update_cell(i + 1, rating_col, "N/A")
        print(f"❌ {title}: Not found")

    time.sleep(1.5)  # Be polit