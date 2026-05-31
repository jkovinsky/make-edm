# make-edm

Automated pipeline that creates weekly Spotify playlists of EDM artists performing in major US cities, sourced from [19hz.info](https://19hz.info).

## Pipeline

Run `python main.py` to execute all steps across all 16 supported cities:

1. **Scrape** (`get_page.py`): scrapes upcoming events from 19hz for a given city URL
2. **Parse** (`llm.py`): sends events to Google Gemini (batch API) to extract artist names and dates as structured JSON
3. **Filter** (`main.py`): keeps only events happening the current week
4. **Search Spotify** (`search_artists.py`): looks up each artist on Spotify to validate the search term, storing IDs
5. **Rank** (`rank_artist.py`): scores each artist 1–10 via Gemini based on EDM artist tier
6. **Fetch tracks** (`get_tracks.py`): pulls tracks per artist, weighted by their score
7. **Create playlist** (`create_playlist.py`): Flask app that handles Spotify OAuth and creates/populates the final playlist

Steps 1–6 run for each city with a 1-hour wait between cities. Output is written to:

```
cities/
└── {city}/
    └── {week-range}/
        ├── candidates.json
        ├── this_week.json
        ├── spotify_results.json
        └── tracks_this_week.json
```

## Creating a Playlist

After the pipeline runs, start the Flask app with the city and week you want:

```
python create_playlist.py --city "Los Angeles" --week "2026-05-25_2026-05-31"
```

Then visit `http://127.0.0.1:5001` to authorize Spotify and create the playlist.

## Supported Cities

San Francisco Bay Area, Los Angeles, Seattle, Atlanta, Miami, Washington DC, Toronto, Iowa/Nebraska, Texas, Denver, Chicago, Detroit, Massachusetts, Phoenix, Portland/Oregon, Vancouver

## Tech Stack

- Python, Flask
- Google Gemini batch API (structured output via Pydantic)
- Spotify Web API

## Setup

This pipeline assumes you have already:

- Created a [Spotify Developer](https://developer.spotify.com/dashboard) project and obtained a client ID and secret
- Created a [Google Gemini](https://aistudio.google.com/app/apikey) API key

Install dependencies:

```
pip install -r requirements.txt
```

Create `.env` and fill in:

```
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
GOOGLE_GEMINI_API_KEY=
```
