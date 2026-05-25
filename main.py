import llm, get_page, spotify, json
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time

load_dotenv() 
def save(data):
    with open('candidates.json', 'w') as f:
        json.dump(data, f, indent=4)

def is_this_week(date_str : str) -> bool:
    try:

        event_date = datetime.strptime(date_str.split('T')[0], "%Y-%m-%d")
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return start_of_week <= event_date <= end_of_week
    except ValueError:
        print(f"Invalid date format: {date_str}")
        return False

if __name__ == "__main__":
    this_week = []
    events = get_page.events()
    # structured_artists = llm.parse_artist(events)

    with open('candidates.json', 'r') as f:
        structured_artists = json.load(f)
    
    for item in structured_artists:
        date = item[0].get('date', '')
        if is_this_week(date):
            this_week.append(item)
            # print(f"Event on {date} is happening this week!")
        else:
            pass
            # print(f"Event on {date} is NOT happening this week.")
    
    with open('this_week.json', 'w') as f:
        json.dump(this_week, f, indent=4)
    '''
    candididates = {'artists': []}
    for item in structured_artists:
        exit()
        artists = item.get('artists', [])
        date    = item.get('date', '')
        if not artists:
            print(f"No artists found for event on {date}. Skipping...")
            continue
        for artist in artists:
            print(artist)
            spotify_response = spotify.search_artist(artist, date)
            if spotify_response['id']:
                if spotify_response['name_returned'].lower() == artist.lower():
                    candididates['artists'].append({artist: spotify_response})
                    print(f"Spotify hash for {artist}: {spotify_response}")
                else:
                    print(f"Spotify returned a different name for {artist}: {spotify_response['name_returned']}")
            else:
                print(f"No Spotify match found for {artist}")
            save(candididates)
            time.sleep(10)
    '''