import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Tuple, Optional

from config import load_config
from zbx_api import ZabbixClient
from summarizer import summarize
from deliver import deliver

def unix_now() -> int:
    return int(datetime.now(timezone.utc).timestamp())

def load_state(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_state(path: str, state: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def compute_time_from(state: Dict[str, Any], hours_fallback: int) -> Tuple[int, int]:
    now = unix_now()
    last = state.get("last_run_utc")
    if isinstance(last, int) and last > 0:
        return int(last), now
    return now - hours_fallback * 3600, now

import time

def main():
    print("[INFO] Starting Zabbix Real-time Agent...")
    cfg = load_config()
    zbx = ZabbixClient(cfg.api_url, cfg.user, cfg.password)
    
    while True:
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 1. Load state and version
            state = load_state(cfg.state_path)
            api_ver = zbx.api_version()
            time_from, now = compute_time_from(state, cfg.hours)

            # 2. Extract data from Zabbix
            problems = zbx.get_problems(time_from=time_from)
            events = zbx.get_events(time_from=time_from)
            all_hosts = zbx.get_hosts()
            all_triggers = zbx.get_all_triggers()
            
            print(f"[{timestamp}] Zabbix Scan: {len(all_hosts)} hosts and {len(all_triggers)} triggers identified.")

            # 3. Generate Report (Delta Logic inside summarize)
            scan_id = str(uuid.uuid4())
            report, next_processed_findings = summarize(
                scan_id=scan_id,
                company_id=cfg.company_id,
                api_key=cfg.api_key,
                api_version=api_ver,
                problems=problems,
                events=events,
                all_hosts=all_hosts,
                all_triggers=all_triggers,
                state=state
            )

            # 4. Deliver if changes detected
            if report["findings"] or not state.get("processed_findings"):
                new_count = len(report['findings'])
                deliver(cfg.output_mode, report, cfg.webhook_url, cfg.api_key)
                
                with open("debug_report.json", "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
            else:
                print(f"[{timestamp}] No changes detected. Skipping delivery.")

            # 5. Update state
            state["last_run_utc"] = now
            state["processed_findings"] = next_processed_findings
            save_state(cfg.state_path, state)
            
        except Exception as e:
            print(f"[ERROR] Cycle failure: {str(e)}")
            print("[INFO] Retrying in 10 seconds...")
            time.sleep(10)
            continue

        time.sleep(cfg.interval)

if __name__ == "__main__":
    main()
