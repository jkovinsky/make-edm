from dotenv import load_dotenv
from datetime import datetime, timedelta
import json, os, time

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
    "Iowa/Nebraska":          f"{BASE}/eventlisting_Iowa.php",
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


def main():
    today = datetime.now()
    start_of_week = today - timedelta(days=(today.weekday() + 1) % 7)
    end_of_week = start_of_week + timedelta(days=6)
    print(f"Week: {start_of_week.strftime('%Y-%m-%d')} (Sun) – {end_of_week.strftime('%Y-%m-%d')} (Sat)\n")

    week_range = f"{start_of_week.strftime('%Y-%m-%d')}_{end_of_week.strftime('%Y-%m-%d')}"
    all_results = []
    token = spotify.ensure_token()

    cities = list(CITIES.items())
    for i, (city, url) in enumerate(cities):
        print(f"--- {city} ---")

        output_dir = os.path.join('cities', city, week_range)
        os.makedirs(output_dir, exist_ok=True)

        # 1. Scrape events
        print("  Scraping events...")
        events = get_page.events(url)
        print(f"  {len(events)} events found.")

        # 2. Parse artists + dates via Gemini batch
        print("  Parsing artists with LLM...")
        structured = llm.parse_artist(events, output_dir)
        print(f"  {len(structured)} events parsed.")

        # 3. Filter to this week
        this_week = [item for item in structured if is_this_week(item[0].get('date', ''))]
        print(f"  {len(this_week)} events this week.")
        with open(os.path.join(output_dir, 'this_week.json'), 'w') as f:
            json.dump(this_week, f, indent=4)

        # 4. Search Spotify for each artist
        print("  Searching Spotify...")
        results = spotify.search_artists(this_week, token)
        print(f"  {len(results)} artists matched.")

        # 5. Rank artists 1-10 via Gemini batch
        print("  Ranking artists...")
        scores = rank_artist.rank_artists(results, output_dir)
        for artist, score in zip(results, scores):
            artist['popularity'] = score.get('score')
            artist['city'] = city
        print(f"  {len(scores)} artists ranked.")

        with open(os.path.join(output_dir, 'spotify_results.json'), 'w') as f:
            json.dump(results, f, indent=4)

        # 6. Fetch tracks per artist (count based on score)
        print("  Fetching tracks...")
        token = spotify.ensure_token()
        get_tracks.get_tracks(results, token, output_dir)
        print("  Tracks saved.")

        all_results.extend(results)

        if i < len(cities) - 1:
            print("  Waiting 1 hour before next city...")
            time.sleep(3600)

    print("\nPipeline complete. Run `python create_playlist.py` to create the Spotify playlist (requires OAuth).")


if __name__ == "__main__":
    main()
