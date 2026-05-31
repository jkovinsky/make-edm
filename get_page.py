import requests
from bs4 import BeautifulSoup


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