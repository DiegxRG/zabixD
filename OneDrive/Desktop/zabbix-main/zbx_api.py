import time
import requests
from typing import Any, Dict, Optional

class ZabbixClient:
    def __init__(self, api_url: str, user: str, password: str, timeout: int = 30):
        self.api_url = api_url.rstrip("/")
        self.user = user
        self.password = password
        self.timeout = timeout
        self.auth_token = None
        self.session = requests.Session()

    def login(self):
        try:
            # Intentamos formato Zabbix 7.0+ (username)
            resp = self.call("user.login", {"username": self.user, "password": self.password})
        except Exception:
            # Fallback para Zabbix 6.4 y anteriores (user)
            resp = self.call("user.login", {"user": self.user, "password": self.password})
        
        self.auth_token = resp
        return resp

    def call(self, method: str, params: Any) -> Any:
        payload: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": int(time.time()),
        }

        # Evitamos bucle infinito si login falla
        if method not in ("apiinfo.version", "user.login") and not self.auth_token:
            self.login()

        # Configurar Headers
        headers = {"Content-Type": "application/json-rpc"}
        if self.auth_token and method != "apiinfo.version":
            # En Zabbix 7.0 se usa Bearer token incluso para sesiones
            headers["Authorization"] = f"Bearer {self.auth_token}"

        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        r = self.session.post(self.api_url, json=payload, headers=headers, timeout=self.timeout, verify=False)
        r.raise_for_status()
        data = r.json()

        if "error" in data:
            # La doc muestra que en error viene: code/message/data :contentReference[oaicite:7]{index=7}
            raise RuntimeError(f"Zabbix API error: {data['error']}")

        return data["result"]

    def api_version(self) -> str:
        return self.call("apiinfo.version", {})

    def get_problems(self, time_from: int, limit: int = 2000):
        # 1. Obtener los problemas (Zabbix 7.0 no permite selectHosts aquí)
        problems = self.call("problem.get", {
            "output": ["eventid", "name", "severity", "clock", "r_clock", "acknowledged", "objectid"],
            "selectTags": "extend",
            "selectAcknowledges": "extend",
            "time_from": time_from,
            "sortfield": ["eventid"],
            "sortorder": "DESC",
            "limit": limit
        })

        if not problems:
            return []

        # 2. En Zabbix los problemas nacen de Triggers. Vamos a buscar los hosts de esos Triggers.
        trigger_ids = list(set(p["objectid"] for p in problems if p.get("objectid")))
        if trigger_ids:
            triggers = self.call("trigger.get", {
                "triggerids": trigger_ids,
                "selectHosts": ["hostid", "name", "host", "inventory"],
                "output": ["triggerid"]
            })
            
            # Crear un mapa de trigger_id -> hosts
            trigger_map = {t["triggerid"]: t.get("hosts", []) for t in triggers}
            
            # Inyectar los hosts de vuelta en cada problema para que el summarizer no cambie
            for p in problems:
                p["hosts"] = trigger_map.get(p["objectid"], [])
        
        return problems

    def get_hosts(self):
        # Traer todos los hosts habilitados para el censo
        return self.call("host.get", {
            "output": ["hostid", "name", "host", "status"],
            "selectInventory": "extend",
            "selectInterfaces": "extend",
            "filter": {"status": "0"} # Solo hosts monitoreados
        })

    def get_system_info(self):
        # Información general del sistema Zabbix
        try:
            return self.call("apiinfo.version", {})
        except:
            return "unknown"

    def get_all_triggers(self, limit: int = 5000):
        # Solo traer triggers de hosts monitoreados (para evitar basura de templates)
        return self.call("trigger.get", {
            "output": ["triggerid", "description", "priority", "status", "lastchange"],
            "selectHosts": ["hostid", "name", "host", "inventory"],
            "selectInterfaces": ["ip", "port", "main"],
            "selectTags": "extend",
            "monitored": True, # <--- IMPORTANTE: Solo hosts reales
            "filter": {"status": "0"}, 
            "limit": limit
        })

    def get_events(self, time_from: int, limit: int = 2000):
        return self.call("event.get", {
            "output": ["eventid", "name", "severity", "clock", "value"],
            "time_from": time_from,
            "sortfield": ["eventid"],
            "sortorder": "DESC",
            "limit": limit,
        })
