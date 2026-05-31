from dotenv import load_dotenv
from datetime import datetime, timedelta
import json

import get_page
import llm
import search_artists as spotify
import rank_artist
import get_tracks

load_dotenv()


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
    # 1. Scrape events
    print("Scraping events from 19hz...")
    events = get_page.events()
    print(f"  {len(events)} events found.")

    # 2. Parse artists + dates via Gemini batch
    print("Parsing artists with LLM...")
    structured = llm.parse_artist(events)
    print(f"  {len(structured)} events parsed.")

    # 3. Filter to this week
    today = datetime.now()
    start_of_week = today - timedelta(days=(today.weekday() + 1) % 7)
    end_of_week = start_of_week + timedelta(days=6)
    print(f"  Week: {start_of_week.strftime('%Y-%m-%d')} (Sun) – {end_of_week.strftime('%Y-%m-%d')} (Sat)")
    this_week = [item for item in structured if is_this_week(item[0].get('date', ''))]
    print(f"  {len(this_week)} events happening this week.")
    with open('this_week.json', 'w') as f:
        json.dump(this_week, f, indent=4)

    # 4. Search Spotify for each artist
    print("Searching Spotify for artists...")
    token = spotify.ensure_token()
    results = spotify.search_artists(this_week, token)
    print(f"  {len(results)} artists matched on Spotify.")
    with open('spotify_results.json', 'w') as f:
        json.dump(results, f, indent=4)

    # 5. Rank artists 1-10 via Gemini batch
    print("Ranking artists...")
    scores = rank_artist.rank_artists(results)
    for artist, score in zip(results, scores):
        artist['popularity'] = score.get('score')
    with open('spotify_results.json', 'w') as f:
        json.dump(results, f, indent=4)
    print(f"  {len(scores)} artists ranked.")

    # 6. Fetch tracks per artist (count based on score)
    print("Fetching tracks...")
    token = spotify.ensure_token()
    get_tracks.get_tracks(results, token)
    print("  Tracks saved to tracks_this_week.json.")

    print("\nPipeline complete. Run `python create_playlist.py` to create the Spotify playlist (requires OAuth).")


if __name__ == "__main__":
    main()
