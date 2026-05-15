import json
import os


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


def read_current_status(current_path: str) -> tuple[str, str]:
    """Lee status y action del current_state.json. Retorna ('—', '—') si no existe."""
    if not os.path.exists(current_path):
        return "—", "—"
    with open(current_path, "r", encoding="utf-8") as f:
        data = extract_json_body(f.read())
    loyalty = data.get("loyaltyData", {})
    return loyalty.get("status", "—").upper(), loyalty.get("action", "—").upper()
