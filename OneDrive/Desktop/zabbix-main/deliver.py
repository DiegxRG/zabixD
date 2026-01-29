import json
import requests
from typing import Optional

def send_stdout(text: str) -> None:
    print(text)

def send_webhook(webhook_url: str, text: str) -> None:
    # Slack/Teams/Discord: la mayoría acepta {"text":"..."} o similar
    payload = {"text": text}
    r = requests.post(webhook_url, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=30)
    r.raise_for_status()

def deliver(mode: str, report: str, webhook_url: Optional[str]) -> None:
    if mode in ("stdout", "all"):
        send_stdout(report)

    if mode in ("webhook", "all"):
        if not webhook_url:
            raise SystemExit("OUTPUT_MODE=webhook/all pero falta WEBHOOK_URL")
        send_webhook(webhook_url, report)
