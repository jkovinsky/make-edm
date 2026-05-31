from dotenv import load_dotenv
import requests, os, time, json, csv, base64, time
from datetime import datetime

load_dotenv()

CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
TOKEN_URL     = 'https://accounts.spotify.com/api/token'
API_BASE_URL  = 'https://api.spotify.com/v1'
REDIRECT_URI = 'http://127.0.0.1:5001/callback'
TOKEN_FILE    = 'spotify_token.csv'

def fetch_token():
    credentials = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    req_body = {
        'grant_type' : 'client_credentials'
    }
    response = requests.post(TOKEN_URL, data=req_body,
                             headers={'Authorization': f'Basic {credentials}'})
    token_info = response.json()

    access_token = token_info['access_token']
    expires_at   = datetime.now().timestamp() + token_info['expires_in']

    save_token(access_token, expires_at)
    return access_token, expires_at


def save_token(access_token, expires_at):
    with open(TOKEN_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['access_token', 'expires_at'])
        writer.writerow([access_token, expires_at])


def load_token():
    try:
        with open(TOKEN_FILE, 'r') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            return row['access_token'], float(row['expires_at'])
    except (FileNotFoundError, StopIteration, KeyError):
        return None, None


def ensure_token():
    access_token, expires_at = load_token()

    if datetime.now().timestamp() > expires_at:
        access_token, _ = fetch_token()

    return access_token

def get_tracks(artists, token):
    headers = {'Authorization' : f'Bearer {token}'}
    spotify_track_uris = []

    limits = {(8, 10): 3, (5, 7): 2, (3, 4): 1}
    for artist in artists:
        score = artist.get('popularity')
        limit = next((n for (low, high), n in limits.items() if score and low <= score <= high), 0)
        if not limit:
            continue

        response = requests.get(API_BASE_URL + '/search', headers=headers,
                                params={"q": artist['match_name'], "type": "track", "limit": limit})
        time.sleep(1)

        if not response.ok:
            print(f"Spotify error {response.status_code} for '{artist['match_name']}'")
            continue

        items = response.json().get('tracks', {}).get('items', [])
        for item in items:
            if item['type'] == 'track':
                spotify_track_uris.append(item['uri'])
    
    with open('tracks_this_week.json', 'w') as f:
        json.dump(spotify_track_uris, f, indent=4)

if __name__ == "__main__":

    with open('this_weeks_playlist.json', 'r') as f:
        artists = json.load(f)
    
    token = ensure_token()

    get_tracks(artists, token)
