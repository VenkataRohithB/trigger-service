import time
import requests
from datetime import datetime, timedelta
from pubsub_helper import PubSub

FETCH_URL = "http://localhost:8989/triggered_events/current_time"
UPDATE_URL = "http://localhost:8989/triggered_logs/update_and_delete"


def fetch_triggered_events():
    """Fetch records from triggered_events API."""
    try:
        response = requests.get(FETCH_URL, timeout=5, headers=HEADERS)
        data = response.json()

        if response.status_code == 200 and data.get("status_bool"):
            return data.get("records", [])
        else:
            print(f"No records found: {data}")
            return []
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return []


def update_and_delete():
    """Calls the update_and_delete API."""
    try:
        response = requests.patch(UPDATE_URL, timeout=5, headers=HEADERS)
        print(f"Update API Response: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"Failed to call update API: {e}")


def wait_until_next_minute():
    """Wait until the next minute starts exactly."""
    now = datetime.now()
    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    sleep_time = (next_minute - now).total_seconds()
    time.sleep(sleep_time)


def worker():
    """Background task worker that runs exactly at the start of every minute."""
    conn = PubSub(topic="TRIGGER_EVENTS")
    wait_until_next_minute()

    while True:
        records = fetch_triggered_events()
        for record in records:
            conn.publish(msg_dict=record)

        update_and_delete()
        wait_until_next_minute()


if __name__ == "__main__":
    TOKEN_URL = "http://localhost:8989/generate_token?passcode=11923"

    try:
        token_response = requests.get(url=TOKEN_URL, timeout=5).json()
        TOKEN = token_response["records"][0]["token"]
        HEADERS = {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        }
    except (requests.RequestException, KeyError, IndexError) as e:
        print(f"Failed to fetch token: {e}")
        TOKEN = None
    if TOKEN:
        worker()
    else:
        print("Exiting due to missing token.")
