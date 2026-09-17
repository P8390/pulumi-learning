import requests
import os
import time
from datetime import datetime, timedelta
import json
from datetime import date

teams_webhook = os.environ["TEAMS_WEBHOOK_URL"]
token = os.environ['GH_TOKEN']
org = os.environ['ORG']

print(f"Org: {org}")
current_timestamp = int(time.time() * 1000)
print(f"Current timestamp: {current_timestamp}")

def send_teams_message(message: str):
    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.2",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": "🚨 GitHub Org Owner Change Detected",
                            "weight": "Bolder",
                            "size": "Medium"
                        },
                        {
                            "type": "TextBlock",
                            "text": message,
                            "wrap": True
                        }
                    ]
                }
            }
        ]
    }
    response = requests.post(teams_webhook, json=payload)
    response.raise_for_status()
    print(f"Teams message sent: {message}")

def is_older_than_10_minutes(ts_ms: int) -> bool:
    ts = datetime.fromtimestamp(ts_ms / 1000.0)
    now = datetime.now()
    ten_minutes_ago = now - timedelta(minutes=10)
    return ts < ten_minutes_ago

def filter_logs(data):
    # Fix 1: Handle API error responses
    if isinstance(data, dict):
        print(f"GitHub API Error: {data.get('message', 'Unknown error')}")
        exit(1)

    if not isinstance(data, list):
        print(f"Unexpected data format: {type(data)}")
        exit(1)

    if len(data) == 0:
        print("No audit log entries found for today.")
        exit(0)

    print(f"Total log entries fetched: {len(data)}")

    for index in data:
        timestamp = int(index["@timestamp"])
        print(f"Processing log timestamp: {timestamp}")

        # Fix 2: Use continue instead of exit so older entries don't stop processing
        if is_older_than_10_minutes(timestamp):
            print("Entry older than 10 minutes, skipping.")
            continue

        operation_type = index.get("operation_type")
        if operation_type == "remove":
            continue

        actor = index.get("actor", "unknown")
        user = index.get("user", "unknown")
        permission = index.get("permission", "")

        if operation_type == "create" and permission == "admin":
            message = f"🚨 {user} is added as admin in {org} org"
            send_teams_message(message)

        if operation_type == "modify" and permission == "admin":
            message = f"🚨 {user} has been promoted as admin for {org} org by {actor}"
            send_teams_message(message)

        # Fix 3: Specific exception handling
        try:
            old_permission = index["old_permission"]
            if old_permission == "admin" and permission == "read":
                message = f"🚨 {user} has been demoted from admin to member for {org} org by {actor}"
                send_teams_message(message)
        except KeyError:
            pass

today = date.today()
formatted_date = today.strftime("%Y-%m-%d")

def audit_logs():
    url = (
        f"https://api.github.com/orgs/{org}/audit-log"
        f"?phrase=action:org.add_member action:org.remove_member action:org.update_member"
        f"&created:>={formatted_date}"
    )

    # Fix 4: Correct Accept header for audit log API
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json'
    }

    print(f"Fetching audit logs from: {url}")
    response = requests.get(url, headers=headers)

    # Fix 5: Print status for debugging
    print(f"API Status Code: {response.status_code}")

    if response.status_code != 200:
        print(f"API Error Response: {response.text[:500]}")
        exit(1)

    data = response.json()
    return data

data = audit_logs()
filter_logs(data)
