from dotenv import load_dotenv
from flask import Flask, request, redirect, jsonify, session, render_template_string
import requests, os, base64, time, csv, urllib.parse, json
from datetime import datetime

load_dotenv()

TOKEN_FILE = 'spotify_token.csv'
CLIENT_ID  = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = 'http://127.0.0.1:5001/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1'
TESTING = '4mncDFjVLUa3s025Tct3Ry'

app = Flask(__name__)
app.secret_key = '53df9b8c-8c9e-4a1b-9d2e-1a2b3c4d5e6f'  # Replace with a secure random key in production

def get_week_range():
    with open('spotify_results.json', 'r') as f:
        artists = json.load(f)
    
    dates = [datetime.strptime(artist['date'].split('T')[0], "%Y-%m-%d") for artist in artists]

    return str(min(dates)).split(' ')[0],  str(max(dates)).split(' ')[0]

@app.route('/')
def index():
    return 'welcome to jake\'s bay area playlist maker !<a href="/login"> Login with Spotify</a>'

@app.route('/login')
def login():
    scope = 'user-read-private user-read-email playlist-modify-public playlist-modify-private'

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog' : True,
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})
    
    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        }
    
    response = requests.post(TOKEN_URL, data=req_body)
    token_info = response.json()

    session['access_token'] = token_info['access_token']
    session['refresh_token'] = token_info['refresh_token']
    session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

    return redirect('/create-playlist')

@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')
    
    print(session['access_token'])
    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type' : 'refresh_token',
            'refresh_token' : session['refresh_token'],
            'client_id' : CLIENT_ID,
            'client_secret' : CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        return redirect('/create-playlist')


@app.route('/create-playlist')
def create_playlist():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')

    headers = {
        'Authorization' : f"Bearer {session['access_token']}",
        'Content-Type' : "application/json"
    }

    start_date, end_date = get_week_range()

    name = f"Los Angeles/SoCal EDM: {start_date} - {end_date}"
    description = "A few songs from artists performing in Los Angeles/SoCal that I discovered this week from 19hz"
    body = {
        "name" : name,
        "description" : description,
        "public" : True
    }

    response = requests.post(API_BASE_URL + '/me/playlists', headers=headers, json=body)
    playlist_id = response.json()["id"]
    with open('tracks_this_week.json', 'r') as f:
        tracks = json.load(f)

    body = {
        "uris" : tracks
    }
    response = requests.post(API_BASE_URL + f'/playlists/{playlist_id}/items', headers=headers, json=body).json()

    return jsonify(response)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)