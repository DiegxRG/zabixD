import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

@dataclass(frozen=True)
class Config:
    api_url: str
    user: str
    password: str
    hours: int
    output_mode: str  # stdout | webhook | all
    webhook_url: Optional[str]
    state_path: str
    company_id: int
    api_key: str
    interval: int # Segundos entre escaneos

def load_config() -> Config:
    load_dotenv()

    # Zabbix Source
    api_url = os.getenv("ZABBIX_API_URL", "").strip()
    user = os.getenv("ZABBIX_USER", "").strip()
    password = os.getenv("ZABBIX_PASS", "").strip()
    hours = int(os.getenv("HOURS", "24"))
    
    # Backend TxDxAI (Prioridad a TXDXAI_*)
    output_mode = os.getenv("OUTPUT_MODE", "stdout").strip().lower()
    webhook_url = os.getenv("TXDXAI_INGEST_URL") or os.getenv("WEBHOOK_URL")
    company_id = int(os.getenv("TXDXAI_COMPANY_ID") or os.getenv("COMPANY_ID", "1"))
    api_key = os.getenv("TXDXAI_API_KEY") or os.getenv("API_KEY", "local_test_key")
    
    state_path = os.getenv("STATE_FILE") or os.getenv("STATE_PATH", "./state.json")
    interval = int(os.getenv("INTERVAL", "60"))

    if not api_url:
        raise SystemExit("Falta ZABBIX_API_URL.")
    if not user or not password:
        raise SystemExit("Faltan ZABBIX_USER o ZABBIX_PASS.")
    
    return Config(
        api_url=api_url,
        user=user,
        password=password,
        hours=hours,
        output_mode=output_mode,
        webhook_url=webhook_url.strip() if webhook_url else None,
        state_path=state_path,
        company_id=company_id,
        api_key=api_key.strip(),
        interval=interval
    )
