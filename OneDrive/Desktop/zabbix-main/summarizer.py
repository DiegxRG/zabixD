from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List

SEVERITY_LABEL = {
    0: "Not classified",
    1: "Information",
    2: "Warning",
    3: "Average",
    4: "High",
    5: "Disaster",
}

def _ts(ts: int) -> str:
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

def summarize(hours_window: int, api_version: str, problems: List[Dict[str, Any]], events: List[Dict[str, Any]]) -> str:
    sev_counts = Counter()
    host_counts = Counter()
    open_count = 0
    ack_count = 0

    for p in problems:
        sev = int(p.get("severity", 0))
        sev_counts[sev] += 1

        if int(p.get("r_clock") or 0) == 0:
            open_count += 1
        if int(p.get("acknowledged", 0)) == 1:
            ack_count += 1

        for h in (p.get("hosts") or []):
            host_counts[h.get("name", "unknown")] += 1

    top_hosts = host_counts.most_common(5)
    now = int(datetime.now(timezone.utc).timestamp())

    lines: List[str] = []
    lines.append(f"# Resumen Zabbix (últimas {hours_window}h)")
    lines.append(f"- Generado (UTC): **{_ts(now)}**")
    lines.append(f"- API version: **{api_version}**")
    lines.append("")
    lines.append("## Salud general")
    lines.append(f"- Problemas: **{len(problems)}**")
    lines.append(f"- Abiertos (estimado): **{open_count}**")
    lines.append(f"- Acknowledged: **{ack_count}**")
    lines.append(f"- Eventos: **{len(events)}**")
    lines.append("")
    lines.append("## Severidad (problemas)")
    if not sev_counts:
        lines.append("- Sin problemas en el rango.")
    else:
        for sev in sorted(sev_counts.keys(), reverse=True):
            lines.append(f"- {SEVERITY_LABEL.get(sev, str(sev))}: **{sev_counts[sev]}**")
    lines.append("")
    lines.append("## Top hosts (por problemas)")
    if not top_hosts:
        lines.append("- (sin datos)")
    else:
        for host, c in top_hosts:
            lines.append(f"- {host}: **{c}**")
    lines.append("")
    lines.append("## Últimos 7 problemas")
    for p in problems[:7]:
        sev = int(p.get("severity", 0))
        hosts = ", ".join([h.get("name", "unknown") for h in (p.get("hosts") or [])]) or "(sin host)"
        lines.append(f"- [{SEVERITY_LABEL.get(sev, sev)}] {p.get('name','')} — {hosts} — {_ts(int(p.get('clock',0)))}")

    return "\n".join(lines) + "\n"
