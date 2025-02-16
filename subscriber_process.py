import requests
import time
from pubsub_helper import PubSub


def on_message(msg):
    """
    Callback function triggered when a message is received.
    It sends a POST request with the trigger_id from the message.
    """
    API_URL = "http://localhost:8989/triggered_events/log_event"
    if not isinstance(msg, dict) or "id" not in msg:
        print("Invalid message format:", msg)
        return

    trigger_id = msg["id"]
    post_url = f"{API_URL}?trigger_id={trigger_id}"

    try:
        response = requests.post(post_url, timeout=5, headers=HEADERS)
        response_data = response.json()
        print(f"POST {post_url} → Status: {response.status_code}, Response: {response_data}")
    except requests.RequestException as e:
        print(f"Failed to send POST request for trigger_id {trigger_id}: {e}")


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
        TOKEN = None  # Set a default value or exit

    if TOKEN:
        print("Starting subscriber background task...")
        conn = PubSub("TRIGGER_EVENTS")
        conn.subscribe(callback_function=on_message)

    else:
        print("Exiting due to missing token.")
