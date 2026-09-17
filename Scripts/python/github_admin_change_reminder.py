import requests
import os
import time
from datetime import datetime, timedelta
import json
from datetime import date

teams_webhook = os.environ["TEAMS_WEBHOOK_URL"]
token = os.environ['GH_TOKEN']
org = os.environ['ORG']
print(org)

current_timestamp = int(time.time() * 1000)

print(current_timestamp)


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


def is_older_than_10_minutes(ts_ms: int) -> bool:
    # Convert timestamp (ms) → datetime
    ts = datetime.fromtimestamp(ts_ms / 1000.0)

    # Current time
    now = datetime.now()

    # 10 minutes ago
    ten_minutes_ago = now - timedelta(minutes=10)

    return ts < ten_minutes_ago


def filter_logs(data):
    for index in data:
        timestamp = int(index["@timestamp"])
        print(timestamp)
        check_timestamp = is_older_than_10_minutes(timestamp)
        if check_timestamp == True:
            exit(0)
        operation_type = index["operation_type"]
        if operation_type == "remove":
            continue
        actor = index["actor"]
        user = index["user"]
        permission = index["permission"]
        if operation_type == "create" and permission == "admin":
            message = f"🚨 GitHub Org Owner Change Detected -> {user} is added as admin in {org} org"
            send_teams_message(message)
        if operation_type == "modify" and permission == "admin":
            message = f"🚨 GitHub Org Owner Change Detected -> {user} has been promoted as admin for {org} org by {actor}"
            send_teams_message(message)
        try:
            old_permission = index["old_permission"]
            if old_permission == "admin" and permission == "read":
                message = f"🚨 GitHub Org Owner Change Detected -> {user} has been demoted from admin to member for {org} org by {actor}"
                send_teams_message(message)
        except:
            pass


today = date.today()
formatted_date = today.strftime("%Y-%m-%d")


def audit_logs():
    url = f"https://api.github.com/orgs/{org}/audit-log?phrase=action:org.add_member action:org.remove_member action:org.update_member created:>={formatted_date}"

    payload = {}
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    data = json.loads(response.text)
    return data


data = audit_logs()
filter_logs(data)
