import types, time
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import os, json

def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd, flush=True)
    if iteration == total:
        print()

def convert(seconds):
    min, sec = divmod(seconds, 60)
    hour, min = divmod(min, 60)
    return "%02d:%02d:%02d" % (hour, min, sec)

PROMPT = """
Rank the given electronic music artist on a scale of 1-10 based on the following schema:

Score Range | What it Means | Examples
8 - 10      | Global Superstars / Household Names | Martin Garrix, Tiësto, Skrillex, Armin van Buuren
5 - 7       | Mainstream Niche / Major Indie Acts | Fred again.., John Summit, RÜFÜS DU SOL, Subtronics
3 - 4       | Cult Favorites / Subgenre Royalty   | Magic Sword, Gunship, Sara Landry, Lane 8
1 - 2       | Underground / Local Scene           | Up-and-coming club DJs, producers with small Bandcamp pages

Artist to rank: [INSERT EDM ARTIST NAME HERE]
"""

class Ranking(BaseModel):
    score: int = Field(description="The score of the artist, dj, or producer")

def batch_requests(artists : list[dict]) -> list[dict]:
    try:
        inline_requests = []
        for i, artist in enumerate(artists):
            req = {
                "contents": [{"parts": [{"text": PROMPT.replace("[INSERT EDM ARTIST NAME HERE]", artist["match_name"])}]}],
                'config': {
                    "response_mime_type": "application/json",
                    "response_schema": Ranking
                }
            }
            inline_requests.append(req)
    except Exception as error:
        print(f"Unexpected error while writing batch requests: {error}")
        return []
    return inline_requests


def rank_artists(events: list[dict], output_dir: str = '.') -> list[dict]:
    date_now = datetime.now().strftime("%Y-%m-%d")
    client = genai.Client(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))
    client_response = []
    inline_requests = batch_requests(events)

    if not inline_requests:
        print("Failed to create batch requests.")
        return client_response

    try:
        # Upload the file to the File API
        inline_batch_job = client.batches.create(
            model="gemini-3.1-flash-lite",
            src=inline_requests,
            config={"display_name": f"inline-batch-job-{date_now}"},
        )
        # wait for the job to finish
        job_name = inline_batch_job.name
        if not job_name:
            print("Batch job creation failed.")
            return client_response
        print(f"Polling status for job: {job_name}")

        while True:
            batch_job_inline = client.batches.get(name=job_name)
            if batch_job_inline.state.name in ('JOB_STATE_SUCCEEDED', 'JOB_STATE_FAILED', 'JOB_STATE_CANCELLED', 'JOB_STATE_EXPIRED'):
                print()
                break
            wait = 30
            for elapsed in range(wait):
                remaining = wait - elapsed
                printProgressBar(elapsed, wait, prefix=f'{batch_job_inline.state.name}:', suffix=f'{convert(remaining)} remaining', length=40)
                time.sleep(1)
             
        # print the response
        for i, inline_response in enumerate(batch_job_inline.dest.inlined_responses, start=1):
            # print(f"\n--- Response {i} ---")
            # Check for a successful response
            if inline_response.response:
                # The .text property is a shortcut to the generated text.
               # print(inline_response.response.text)
                try:
                    parsed_response = json.loads(inline_response.response.text)
                    client_response.append(parsed_response)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON response: {e}")
            else:
                print(f"Request {i} failed with error: {inline_response.error}")

        
    except Exception as error:
        print(f"Unexpected: {error}")
        return client_response
    
    with open(os.path.join(output_dir, 'candidates.json'), 'w') as f:
        json.dump(client_response, f, indent=4)

    return client_response


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    with open('spotify_results.json', 'r') as f:
        artists = json.load(f)

    scores = rank_artists(artists)

    for artist, result in zip(artists, scores):
        artist['popularity'] = result.get('score')

    with open('spotify_results.json', 'w') as f:
        json.dump(artists, f, indent=4)

    print(f"Updated popularity for {len(scores)} artists.")
