import llm, get_page, token, json
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time

load_dotenv() 

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
        # print(item)
        date = item[0].get('date', '')
        if is_this_week(date):
            this_week.append(item)
            # print(f"Event on {date} is happening this week!")
        else:
            pass
            # print(f"Event on {date} is NOT happening this week.")

    with open('this_week.json', 'w') as f:
        json.dump(this_week, f, indent=4)

