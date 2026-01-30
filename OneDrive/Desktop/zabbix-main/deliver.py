import json
import requests
from typing import Optional

from typing import Optional, Any, Dict

def send_stdout(data: Any) -> None:
    if isinstance(data, dict):
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(data)

def send_webhook(webhook_url: str, payload: Dict[str, Any], api_key: Optional[str] = None) -> None:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key
    
    try:
        r = requests.post(webhook_url, json=payload, headers=headers, timeout=30)
        if r.status_code >= 400:
            print(f"[ERROR] Webhook rejected ({r.status_code}): {r.text}")
        r.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Critical delivery failure: {str(e)}")
        raise

def deliver(mode: str, report: Any, webhook_url: Optional[str], api_key: Optional[str] = None) -> None:
    if mode == "stdout":
        send_stdout(report)
        return

    if mode in ("webhook", "all"):
        if not webhook_url:
            raise SystemExit("[ERROR] OUTPUT_MODE requires WEBHOOK_URL")
        
        print(f"[INFO] Synchronizing data with TxDxAI Backend...")
        payload = {"text": report} if isinstance(report, str) else report
        send_webhook(webhook_url, payload, api_key)
        print("[SUCCESS] Data ingestion completed.")

    if mode == "all":
        with open("last_payload_sent.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
