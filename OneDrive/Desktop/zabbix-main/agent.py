import json
import os
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
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(path: str, state: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def compute_time_from(state: Dict[str, Any], hours_fallback: int) -> Tuple[int, int]:
    now = unix_now()
    last = state.get("last_run_utc")
    if isinstance(last, int) and last > 0:
        # ventana incremental desde última ejecución (evita duplicados)
        return int(last), now
    # primera corrida: usa HOURS
    return now - hours_fallback * 3600, now

def main():
    cfg = load_config()
    zbx = ZabbixClient(cfg.api_url, cfg.token)
    api_ver = zbx.api_version()

    state = load_state(cfg.state_path)
    time_from, now = compute_time_from(state, cfg.hours)

    # Para mostrar “últimas X horas” en el título, calculamos la ventana real
    window_hours = max(1, int((now - time_from) / 3600))

    problems = zbx.get_problems(time_from=time_from)
    events = zbx.get_events(time_from=time_from)

    report = summarize(window_hours, api_ver, problems, events)

    deliver(cfg.output_mode, report, cfg.webhook_url)

    state["last_run_utc"] = now
    save_state(cfg.state_path, state)

if __name__ == "__main__":
    main()
