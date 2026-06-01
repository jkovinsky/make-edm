import types, time
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import os, json

BATCH_FILE = 'my-batch-requests.jsonl'

PROMPT = """Extract the artist names and date of performance from the following event listing.
            If there is a date range, use the last date.
            Convert the date to YYYY-MM-DD format (assume the current year is 2026).
            If there is no artist name, return an empty list.
        """

class EventInfo(BaseModel):
    artists: List[str] = Field(description="List of artist names extracted from the event listing")
    date: datetime = Field(description="Date of performance in YYYY-MM-DD format")

def batch_requests(events : list[dict]) -> list[dict]:
    try:
        inline_requests = []
        for i, event in enumerate(events):
            req = {
                "contents": [{"parts": [{"text": f"{PROMPT}\n\nEvent listing: {event['date']} | {event['name']}"}]}],
                'config': {
                    "response_mime_type": "application/json",
                    "response_schema": list[EventInfo]
                }
            }
            inline_requests.append(req)
    except Exception as error:
        print(f"Unexpected error while writing batch requests: {error}")
        return []
    return inline_requests


def _sync_parse(client, inline_requests: list) -> list:
    results = []
    for i, req in enumerate(inline_requests, start=1):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=req["contents"],
                config=req["config"],
            )
            results.append(json.loads(response.text))
        except Exception as e:
            print(f"Sync request {i} failed: {e}")
    return results


def parse_artist(events: list[dict], output_dir: str = '.') -> list[dict]:
    date_now = datetime.now().strftime("%Y-%m-%d")
    client = genai.Client(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))
    client_response = []
    inline_requests = batch_requests(events)

    if not inline_requests:
        print("Failed to create batch requests.")
        return client_response

    with open(os.path.join(output_dir, 'events.json'), 'w') as f:
        json.dump(events, f, indent=4)

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

        start_time = time.time()
        timed_out = False
        while True:
            batch_job_inline = client.batches.get(name=job_name)
            if batch_job_inline.state.name in ('JOB_STATE_SUCCEEDED', 'JOB_STATE_FAILED', 'JOB_STATE_CANCELLED', 'JOB_STATE_EXPIRED'):
                break
            if time.time() - start_time > 900:
                print("Batch job timed out after 15 minutes. Cancelling and falling back to synchronous calls...")
                try:
                    client.batches.cancel(name=job_name)
                except Exception as e:
                    print(f"Failed to cancel batch job: {e}")
                client_response = _sync_parse(client, inline_requests)
                timed_out = True
                break
            print(f"Job not finished. Current state: {batch_job_inline.state.name}. Waiting 30 seconds...")
            time.sleep(30)

        if not timed_out:
            for i, inline_response in enumerate(batch_job_inline.dest.inlined_responses, start=1):
                if inline_response.response:
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
    