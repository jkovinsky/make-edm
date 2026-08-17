import os, json

from httpx import __name


BASE_DIR = '/Users/jakekovinsky/Desktop/make-edm/cities'
WEEK = ['2026-05-31_2026-06-06','2026-06-07_2026-06-13']

cache = {}

# Build a cache of artists already sent to Spotify, so we can skip them in the future
city_map = {
    'San Francisco Bay Area': 'sf_bay_area',
    'Los Angeles': 'los_angeles',
    'Seattle': 'seattle',
    'Atlanta': 'atlanta',
    'Miami': 'miami',
    'Washington DC': 'washington_dc',
    'Toronto': 'toronto',
    'Iowa-Nebraska': 'iowa_nebraska',
    'Texas': 'texas',
    'Denver': 'denver',
    'Chicago': 'chicago',
    'Detroit': 'detroit',
    'Massachusetts': 'massachusetts',
    'Phoenix': 'phoenix',
    'Portland': 'portland',
    'Vancouver': 'vancouver',
}

for city, city_key in city_map.items():
    for week in WEEK:
        spotify_results_path = os.path.join(BASE_DIR, city, week, 'spotify_results.json')
        with open(spotify_results_path, 'r') as f:
            spotify_results = json.load(f)

        for artist in spotify_results:
        
            if artist['match_name'] not in cache:
                cache[artist['match_name']] = {
                    'spotify_uri': artist['id'],
                    'spotify_url': artist['url'],
                    'popularity': artist['popularity'],
                    'cities': {},
                    'spotify_tracks' : []
                }
            date = artist['date']
            
            if city_key not in cache[artist['match_name']]['cities']:
                cache[artist['match_name']]['cities'][city_key] = []
            cache[artist['match_name']]['cities'][city_key].append(date)

            tracks = os.path.join(BASE_DIR, city, week, 'tracks_this_week.json')
            with open(tracks, 'r') as f:
                tracks_data = json.load(f)
            for track in tracks_data:
                if track['artist'] == artist['match_name'] and track['uri'] not in cache[artist['match_name']]['spotify_tracks']:
                    cache[artist['match_name']]['spotify_tracks'].append(track['uri'])

if __name__ == "__main__":
    cache_path = '/Users/jakekovinsky/Desktop/make-edm/artist_cache.json'
    with open(cache_path, 'w') as f:
        json.dump(cache, f, indent=2)

print(f"Wrote {len(cache)} artists to {cache_path}")