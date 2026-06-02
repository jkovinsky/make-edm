from dotenv import load_dotenv
from datetime import datetime, timedelta
import argparse, json, os, time

import get_page
import llm
import search_artists as spotify
import rank_artist
import get_tracks

load_dotenv()

BASE = "https://19hz.info"

CITIES = {
    "San Francisco Bay Area": f"{BASE}/eventlisting_BayArea.php",
    "Los Angeles":            f"{BASE}/eventlisting_LosAngeles.php",
    "Seattle":                f"{BASE}/eventlisting_Seattle.php",
    "Atlanta":                f"{BASE}/eventlisting_Atlanta.php",
    "Miami":                  f"{BASE}/eventlisting_Miami.php",
    "Washington DC":          f"{BASE}/eventlisting_DC.php",
    "Toronto":                f"{BASE}/eventlisting_Toronto.php",
    "Iowa-Nebraska":          f"{BASE}/eventlisting_Iowa.php",
    "Texas":                  f"{BASE}/eventlisting_Texas.php",
    "Denver":                 f"{BASE}/eventlisting_Denver.php",
    "Chicago":                f"{BASE}/eventlisting_CHI.php",
    "Detroit":                f"{BASE}/eventlisting_Detroit.php",
    "Massachusetts":          f"{BASE}/eventlisting_Massachusetts.php",
    "Phoenix":                f"{BASE}/eventlisting_Phoenix.php",
    "Portland/Oregon":        f"{BASE}/eventlisting_ORE.php",
    "Vancouver":              f"{BASE}/eventlisting_BC.php",
}
def is_this_week(date_str: str) -> bool:
    try:
        event_date = datetime.strptime(date_str.split('T')[0], "%Y-%m-%d")
        today = datetime.now()
        start_of_week = today - timedelta(days=(today.weekday() + 1) % 7)
        end_of_week = start_of_week + timedelta(days=6)
        return start_of_week <= event_date <= end_of_week
    except ValueError:
        return False


def main(no_wait=False, skip_to=None, wait=3600):
    today = datetime.now()
    start_of_week = today - timedelta(days=(today.weekday() + 1) % 7)
    end_of_week = start_of_week + timedelta(days=6)
    print(f"Week: {start_of_week.strftime('%Y-%m-%d')} (Sun) – {end_of_week.strftime('%Y-%m-%d')} (Sat)\n")

    week_range = f"{start_of_week.strftime('%Y-%m-%d')}_{end_of_week.strftime('%Y-%m-%d')}"
    all_results = []

    cities = list(CITIES.items())
    if args.skip_to is not None:
        cities = cities[args.skip_to:]
        print(f"Skipping to city index {args.skip_to} ({cities[0][0]})")
        
    for i, (city, url) in enumerate(cities):
        print(f"--- {city} ---")

        output_dir = os.path.join('cities', city, week_range)
        os.makedirs(output_dir, exist_ok=True)

        cached = all(os.path.exists(os.path.join(output_dir, f)) for f in ('candidates.json', 'events.json', 'this_week.json'))
        if cached:
            print("  Cache hit — loading from existing files.")
            with open(os.path.join(output_dir, 'this_week.json')) as f:
                this_week = json.load(f)
        else:
            # 1. Scrape events
            print("  Scraping events...")
            events = get_page.events(url)
            print(f"  {len(events)} events found.")

            # 2. Parse artists + dates via Gemini batch
            print("  Parsing artists with LLM...")
            structured = llm.parse_artist(events, output_dir)
            print(f"  {len(structured)} events parsed.")

            # 3. Filter to this week
            this_week = [item for item in structured if item is not None and is_this_week(item[0].get('date', ''))]
            print(f"  {len(this_week)} events this week.")
            with open(os.path.join(output_dir, 'this_week.json'), 'w') as f:
                json.dump(this_week, f, indent=4)

        print(f"  {len(this_week)} events this week.")

        # 4. Search Spotify for each artist
        spotify_results_path = os.path.join(output_dir, 'spotify_results.json')
        if os.path.exists(spotify_results_path):
            print("  Spotify cache hit — loading from spotify_results.json.")
            with open(spotify_results_path) as f:
                results = json.load(f)
        else:
            token = spotify.ensure_token()
            print("  Searching Spotify...")
            results = spotify.search_artists(this_week, token)
            print(f"  {len(results)} artists matched.")

        # 5. Rank artists 1-10 via Gemini batch
        # TODO: add a separate cache file for rankings so ranking can also be skipped independently of spotify_results.json
        if os.path.exists(spotify_results_path):
            print("  Ranking cache hit — skipping ranking.")
        else:
            print("  Ranking artists...")
            scores = rank_artist.rank_artists(results, output_dir)
            for artist, score in zip(results, scores):
                if score is not None:
                    artist['popularity'] = score.get('score')
                artist['city'] = city
            print(f"  {len(scores)} artists ranked.")

            with open(spotify_results_path, 'w') as f:
                json.dump(results, f, indent=4)

        print("  Waiting 3 minutes before fetching tracks to avoid Spotify rate limits...")
        time.sleep(180)  # to avoid hitting rate limits on Spotify API
        print("  done.")
        # 6. Fetch tracks per artist (count based on score)
        tracks_path = os.path.join(output_dir, 'tracks_this_week.json')
        if os.path.exists(tracks_path):
            print("  Tracks cache hit — skipping.")
        else:
            print("  Fetching tracks...")
            token = spotify.ensure_token()
            get_tracks.get_tracks(results, token, output_dir)
            print("  Tracks saved.")

        all_results.extend(results)
        
        if i < len(cities) - 1 and not no_wait:
            if args.wait is not None:
                wait = args.wait
            print(f"  Waiting {wait} seconds before moving to next city...")
            for elapsed in range(wait + 1):
                spotify.printProgressBar(elapsed, wait, prefix='  Next city in:', suffix=spotify.convert(wait - elapsed), length=40)
                if elapsed < wait:
                    time.sleep(1)

    print("\nPipeline complete. Run `python create_playlist.py` to create the Spotify playlist (requires OAuth).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-wait', action='store_true', help='Skip the 1-hour wait between cities')
    parser.add_argument('--skip-to', type=int, help='Skip to a specific city index (0-based)')
    parser.add_argument('--wait-time', type=int, help='Wait time in seconds between cities (default: 3600)')
    args = parser.parse_args()
    main(no_wait=args.no_wait, skip_to=args.skip_to, wait=args.wait_time)
