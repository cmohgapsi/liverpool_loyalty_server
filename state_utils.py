import json
import os
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), "server.log")


def load_env(path: str) -> dict[str, str]:
    """Carga un archivo .env de pares KEY=VALUE, ignora comentarios y líneas vacías."""
    env: dict[str, str] = {}
    if not os.path.exists(path):
        return env
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env


def extract_json_body(raw: str) -> dict:
    """Extrae el JSON de un archivo raw HTTP (ignora la línea de status y headers)."""
    for separator in ("\r\n\r\n", "\n\n"):
        if separator in raw:
            return json.loads(raw.split(separator, 1)[1].strip())
    return json.loads(raw.strip())


def extract_http_status(raw: str) -> int:
    """Extrae el código HTTP de la primera línea de un archivo raw HTTP (ej. HTTP/1.1 404 Not Found → 404)."""
    first_line = raw.strip().splitlines()[0] if raw.strip() else ""
    parts = first_line.split()
    if len(parts) >= 2 and parts[0].startswith("HTTP/"):
        try:
            return int(parts[1])
        except ValueError:
            pass
    return 200


def build_curl(method: str, host: str, port: int, path: str, body: dict | None = None) -> str:
    url   = f"http://{host}:{port}{path}"
    parts = [f'curl -X {method} "{url}"']
    if body is not None:
        parts.append('-H "Content-Type: application/json"')
        parts.append(f"-d '{json.dumps(body, ensure_ascii=False)}'")
    return " ".join(parts)


def log_request(method: str, host: str, port: int, path: str,
                http_code: int, body: dict | None = None, **extras) -> dict:
    entry = {
        "method":           method,
        "path":             path,
        "http_code":        http_code,
        "request_datetime": datetime.now().isoformat(),
        "curl":             build_curl(method, host, port, path, body),
        **extras,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def print_operation_result(prev_status: str, prev_action: str,
                           operation: str, action: str,
                           new_status: str, new_action: str):
    print(f"  ┌{'─' * 85}┐")
    print(f"  │  {'BEFORE':16}  →  status = {prev_status:12} , action = {prev_action:<28} │")
    print(f"  │  {(operation + ' ACTION'):16}  →  {action:<62}│")
    print(f"  │  {'AFTER':16}  →  status = {new_status:12} , action = {new_action:<28} │")
    print(f"  └{'─' * 85}┘")


def resolve_response_file(responses_path: str, url_path: str, filename: str) -> str:
    """Resuelve la ruta del archivo de respuesta.

    Busca primero en responses/<primer-segmento-del-path>/<filename>.
    Si no existe, retorna responses/<filename> como fallback.
    """
    first_segment = url_path.strip("/").split("/")[0]
    override = os.path.join(responses_path, first_segment, filename)
    if os.path.exists(override):
        return override
    return os.path.join(responses_path, filename)


def read_current_status(current_path: str) -> tuple[str, str]:
    """Lee status y action del current_state.json. Retorna ('—', '—') si no existe."""
    if not os.path.exists(current_path):
        return "—", "—"
    with open(current_path, "r", encoding="utf-8") as f:
        data = extract_json_body(f.read())
    loyalty = data.get("loyaltyData", {})
    return loyalty.get("status", "—").upper(), loyalty.get("action", "—").upper()
