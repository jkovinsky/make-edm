from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime
import json


chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.265 Safari/537.36"
)


service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
url = "https://hoer.live/"
driver.get(url)


WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "show-card"))
    )

html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

with open('test_hor_radio.txt', 'w') as f:
    f.write(soup.prettify())

shows = []
for card in soup.find_all("div", class_="show-card"):
    title_div = card.find("div", class_="show-card__title")
    artist_a = title_div.find("a") if title_div else None
    date_div = card.find("div", class_="show-card__date")
    image_a = card.find("a", class_="show-card__image")

    if not artist_a or not date_div:
        continue

    artist_name = artist_a.get_text(strip=True)
    artist_url = "https://hoer.live" + artist_a["href"] if artist_a.get("href") else ""
    show_url = image_a["href"] if image_a and image_a.get("href") else ""

    raw_date = date_div.get_text(strip=True).split("/")[0].strip()
    try:
        date_iso = datetime.strptime(raw_date, "%b %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        date_iso = raw_date

    shows.append({
        "artist": artist_name,
        "artist_url": artist_url,
        "show_url": show_url,
        "date": date_iso,
    })

print(f"Parsed {len(shows)} shows")
for s in shows:
    print(s)

driver.quit()
