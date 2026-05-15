import json
import os


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
