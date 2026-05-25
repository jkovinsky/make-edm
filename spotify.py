from dotenv import load_dotenv
import requests, os, base64, time

load_dotenv()


def get_token():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {credentials}"},
        data={"grant_type": "client_credentials"}
    )
    return response.json()["access_token"]

_token = None

def search_artist(artist_name, date):
    global _token
    if not _token:
        _token = get_token()
    response = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {_token}"},
        params={"q": artist_name, "type": "artist", "limit": 1}
    )

    if response.status_code == 200:
        data = response.json()
        artist = data.get("artists").get("items")
        if artist:
            return {"id": artist[0].get("id"),
                    "name_searched": artist_name,
                    "name_returned": artist[0].get("name"),
                    "date": date,
                    "url": artist[0].get("external_urls").get("spotify")}
        else:
            return {"id": None, "name_searched": artist_name, "name_returned": None, "date": date, "url": None}
    elif response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 30))
        print(f"Rate limited. Retry-After: {retry_after}s — sleeping...")
        time.sleep(retry_after)
        return search_artist(artist_name, date)
    else:
        print(f"Error: {response.status_code}")
        return {"id": None, "name_searched": artist_name, "name_returned": None, "date": date, "url": None}

# print(search_artist("The Weeknd"))