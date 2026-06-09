import requests
from bs4 import BeautifulSoup
from datetime import datetime


def hor_radio_shows(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
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
    return shows


def events(url: str) -> list[dict]:
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        tbody = soup.find('tbody')
        events = []
        for row in tbody.find_all('tr'):
            tds = row.find_all('td')
            if len(tds) >= 2:
                date = tds[0].get_text(separator=' ', strip=True)
                a = tds[1].find('a')
                if a:
                    events.append({
                        'name': a.get_text(strip=True),
                        'url': a['href'],
                        'date': date
                    })
        return events
    else:
        print(f"Error: {response.status_code}")
        return []