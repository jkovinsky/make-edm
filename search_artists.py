from dotenv import load_dotenv
import requests, os, time, json, csv, base64, time, threading
from datetime import datetime

load_dotenv()

CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
TOKEN_URL     = 'https://accounts.spotify.com/api/token'
API_BASE_URL  = 'https://api.spotify.com/v1'
REDIRECT_URI = 'http://127.0.0.1:5001/callback'
TOKEN_FILE    = 'spotify_token.csv'

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd, flush=True)
    # Print New Line on Complete
    if iteration == total:
        print()

def convert(seconds):
    min, sec = divmod(seconds, 60)
    hour, min = divmod(min, 60)
    
    return "%02d:%02d:%02d" % (hour, min, sec)

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


def search_artists(artist_candidates, token):
    headers = {'Authorization' : f'Bearer {token}'}
    spotify_results = []

    total = len(artist_candidates)
    printProgressBar(0, total, prefix='Searching:', suffix='', length=40)
    for i, item in enumerate(artist_candidates, start=1):
        artists = item[0].get('artists')
        date    = item[0].get('date')
        if not artists:
            printProgressBar(i, total, prefix='Searching:', suffix='', length=40)
            continue

        for term in artists:
            response = requests.get(API_BASE_URL + '/search', headers=headers,
                                    params={"q": term, "type": "artist", "limit": 1})
            # print(response.json())
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 1))
                print(f"Rate limited on '{term}', waiting {retry_after}s...")
                for elapsed in range(retry_after + 1):
                    remaining = retry_after - elapsed
                    printProgressBar(elapsed, retry_after, prefix='Progress:', suffix=f'{convert(remaining)} remaining', length=40)
                    if elapsed < retry_after:
                        time.sleep(1)
                time.sleep(60)
                token = ensure_token()
                headers = {'Authorization' : f'Bearer {token}'}
                response = requests.get(API_BASE_URL + '/search', headers=headers,
                                        params={"q": term, "type": "artist", "limit": 1})

            if not response.ok:
                print(f"Spotify error {response.status_code} for '{term}': {response.text}")
                continue

            time.sleep(2)

            artist = response.json().get("artists", {}).get("items")
            if artist:
                if artist[0].get("name", "").lower() == term.lower():
                    artist_id = artist[0].get("id")
                    # full = requests.get(API_BASE_URL + f'/artists/{artist_id}', headers=headers).json()
                    # time.sleep(1)
                    spotify_results.append({
                        "id"         : artist_id,
                        "term"       : term,
                        "match_name" : artist[0].get("name"),
                        "date"       : date,
                        "url"        : artist[0].get("external_urls", {}).get("spotify"),
                        "followers"  : artist[0].get("followers", {}).get("total")
                    })

        printProgressBar(i, total, prefix='Searching:', suffix='', length=40)

    return spotify_results


if __name__ == "__main__":
    with open('this_week.json', 'r') as f:
        artist_candidates = json.load(f)

    token = ensure_token()
    results = search_artists(artist_candidates, token)

    with open('spotify_results.json', 'w') as f:
        json.dump(results, f, indent=4)

    print(f"Found {len(results)} artists. Results written to spotify_results.json.")