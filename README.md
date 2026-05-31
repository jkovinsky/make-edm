# make-edm

Automated pipeline that creates a weekly Spotify playlist of EDM artists performing in major US cities, sourced from [19hz.info](https://19hz.info).

## Pipeline

Run `python main.py` to execute all steps:

1. **Scrape** (`get_page.py`): scrapes upcoming events from 19hz depending on the url provided. Replace `URL` with an event listing from 19hz corresponding to a city.
2. **Parse** (`llm.py`): sends events to Google Gemini (batch API) to extract artist names and dates as structured JSON
3. **Filter**: keeps only events happening the current week, located in `get_artists.py`
4. **Search Spotify** (`search_artists.py`): looks up each artist on Spotify to validate search term, storing IDs
5. **Rank** (`rank_artist.py`): scores each artist 1–10 via Gemini based on edm artist tier
6. **Fetch tracks** (`get_tracks.py`): pulls a limit of tracks per artist, weighted by their score
7. **Create playlist** (`create_playlist.py`): simple Flask app that handles Spotify OAuth and creates/populates the final playlist

## Tech Stack

- Python, Flask
- Google Gemini batch API (structured output via Pydantic)
- Spotify Web API

## Setup

This pipeline assumes you have already:

- Created a [Spotify Developer](https://developer.spotify.com/dashboard) project and obtained a client ID and secret
- Created a [Google Gemini](https://aistudio.google.com/app/apikey) API key

Create `.env` and fill in:

```
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
GOOGLE_GEMINI_API_KEY=
```

Run the pipeline, then start `create_playlist.py` and visit `http://127.0.0.1:5001` to authorize Spotify and create the playlist.
