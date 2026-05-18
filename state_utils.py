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
