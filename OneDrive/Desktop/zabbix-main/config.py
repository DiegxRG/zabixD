import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

@dataclass(frozen=True)
class Config:
    api_url: str
    token: str
    hours: int
    output_mode: str  # stdout | webhook | all
    webhook_url: Optional[str]
    state_path: str

def load_config() -> Config:
    load_dotenv()

    api_url = os.getenv("ZABBIX_API_URL", "").strip()
    token = os.getenv("ZABBIX_TOKEN", "").strip()
    hours = int(os.getenv("HOURS", "24"))
    output_mode = os.getenv("OUTPUT_MODE", "stdout").strip().lower()
    webhook_url = os.getenv("WEBHOOK_URL", "").strip() or None
    state_path = os.getenv("STATE_PATH", "./state.json").strip()

    if not api_url:
        raise SystemExit("Falta ZABBIX_API_URL (debe terminar en /api_jsonrpc.php).")
    if not token:
        raise SystemExit("Falta ZABBIX_TOKEN.")
    if output_mode not in ("stdout", "webhook", "all"):
        raise SystemExit("OUTPUT_MODE debe ser: stdout | webhook | all")

    return Config(
        api_url=api_url,
        token=token,
        hours=hours,
        output_mode=output_mode,
        webhook_url=webhook_url,
        state_path=state_path,
    )
