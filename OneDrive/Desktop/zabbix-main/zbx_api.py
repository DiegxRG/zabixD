import time
import requests
from typing import Any, Dict, Optional

class ZabbixClient:
    def __init__(self, api_url: str, token: str, timeout: int = 30):
        self.api_url = api_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.session = requests.Session()

    def call(self, method: str, params: Any) -> Any:
        payload: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": int(time.time()),
        }

        # Usamos Authorization header (Bearer) como recomienda la doc
        headers = {
            "Content-Type": "application/json-rpc",
            "Authorization": f"Bearer {self.token}",
        }

        r = self.session.post(self.api_url, json=payload, headers=headers, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()

        if "error" in data:
            # La doc muestra que en error viene: code/message/data :contentReference[oaicite:7]{index=7}
            raise RuntimeError(f"Zabbix API error: {data['error']}")

        return data["result"]

    def api_version(self) -> str:
        return self.call("apiinfo.version", {})

    def get_problems(self, time_from: int, limit: int = 2000):
        return self.call("problem.get", {
            "output": ["eventid", "name", "severity", "clock", "r_clock", "acknowledged"],
            "selectHosts": ["name"],
            "time_from": time_from,
            "sortfield": ["clock"],
            "sortorder": "DESC",
            "limit": limit,
            "recent": "true",
        })

    def get_events(self, time_from: int, limit: int = 2000):
        return self.call("event.get", {
            "output": ["eventid", "name", "severity", "clock", "value"],
            "time_from": time_from,
            "sortfield": ["clock"],
            "sortorder": "DESC",
            "limit": limit,
        })
