#!/usr/bin/env python3
"""
Proxyman State Server — Lealtad
Recibe el PATCH redirigido por Map Remote de Proxyman,
actualiza current_state.json y retorna el response apropiado directamente.

Setup en Proxyman:
    Map Remote → PATCH .../pocket-bff/users/me/loyalty/status
              → http://localhost:9876/pocket-bff/users/me/loyalty/status

Uso:
    python3 loyalty_server.py
"""

import json
import os
import shutil
from http.server import HTTPServer, BaseHTTPRequestHandler

# ─── Configura esta ruta ──────────────────────────────────────────────────────
BASE_PATH      = "/Users/carlosmoh/acorde/development/gapsi/lealtad/proxyman/decommission"
STATES_PATH    = os.path.join(BASE_PATH, "states")
RESPONSES_PATH = os.path.join(BASE_PATH, "responses")
CURRENT        = os.path.join(STATES_PATH, "current_state.json")
PORT           = 9876
# ─────────────────────────────────────────────────────────────────────────────

# Mapa de escenarios: (action, value) → (state_file, response_file)
SCENARIOS = {
    ("welcomeModalClosed", True): (
        "enrolled_none_state",
        "path_status_enrolled"
    ),
    ("enrollModalClosed", True): (
        "declined_none_state",
        "path_status_declined"
    ),
    ("unenroll", True): (
        "unenrolled_none_state",
        "path_status_unenroll"
    ),
    ("displayWelcomeModal", True): (
        "enrolled_welcome_state",
        "path_status_enroll_welcome"
    ),
    ("displayEnrollModal", True): (
        "notEnrolled_enroll_state",
        "path_status_notEnrolled_enroll"
    ),
}


def extract_json_body(raw: str) -> dict:
    """Extrae el JSON de un archivo raw HTTP (ignora la línea de status y headers)."""
    for separator in ("\r\n\r\n", "\n\n"):
        if separator in raw:
            return json.loads(raw.split(separator, 1)[1].strip())
    return json.loads(raw.strip())


class LoyaltyHandler(BaseHTTPRequestHandler):

    TARGET_PATH = "/pocket-bff/users/me/loyalty/status"

    def do_GET(self):
        if self.path != self.TARGET_PATH:
            print(f"🔴  404 {self.command} {self.path}")
            print()
            self._respond(404, {"status": {"status": f"NOT FOUND: {self.command} - {self.path}", "statusCode": 404}})
            return
        try:
            print(f"📨  GET {self.path}")
            if not os.path.exists(CURRENT):
                raise FileNotFoundError(f"current_state.json no encontrado en {CURRENT}")
            # ── Leer estado previo ──────────────────────
            prev_status = "—"
            prev_action = "—"
            if os.path.exists(CURRENT):
                with open(CURRENT, "r", encoding="utf-8") as f:
                    prev_data   = extract_json_body(f.read())
                    prev_status = prev_data.get("loyaltyData", {}).get("status", "—").upper()
                    prev_action = prev_data.get("loyaltyData", {}).get("action", "—").upper()
            print(f"  ┌{'─' * 79}┐")
            print(f"  │  {'STATUS':10}  →  status = {prev_status:12} , action = {prev_action:<28} │")
            print(f"  └{'─' * 79}┘")

            with open(CURRENT, "r", encoding="utf-8") as f:
                body = extract_json_body(f.read())

            print(f"📤  Retornando current_state.json")
            self._respond(200, body)
            print()
        except Exception as e:
            print(f"❌  Error: {e}")
            self._respond(500, {"error": str(e)})
            print()

    def do_PATCH(self):
        if self.path != self.TARGET_PATH:
            print(f"🔴  404 {self.command} {self.path}")
            print()
            self._respond(404, {"status": {"status": f"NOT FOUND: {self.command} - {self.path}", "statusCode": 404}})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            data   = json.loads(self.rfile.read(length).decode("utf-8"))

            action = data.get("action", "")
            value  = data.get("value")
            key    = (action, value)

            print(f"📨  PATCH {self.path} → action='{action}', value={value}")

            # ── Sin escenario coincidente ──────────────────────────────────────
            if key not in SCENARIOS:
                print("⚪  Sin escenario coincidente — retornando 200 vacío")
                self._respond(200, {
                    "status": {"status": "OK", "statusCode": 0,
                               "successMessage": "No scenario matched"}
                })
                print()
                return

            state_name, response_name = SCENARIOS[key]

            # ── Leer estado previo antes de sobreescribir ──────────────────────
            prev_status = "—"
            prev_action = "—"
            if os.path.exists(CURRENT):
                with open(CURRENT, "r", encoding="utf-8") as f:
                    prev_data   = extract_json_body(f.read())
                    prev_status = prev_data.get("loyaltyData", {}).get("status", "—").upper()
                    prev_action = prev_data.get("loyaltyData", {}).get("action", "—").upper()

            # ── Actualizar current_state.json ──────────────────────────────────
            src_state = os.path.join(STATES_PATH, f"{state_name}.json")
            if not os.path.exists(src_state):
                raise FileNotFoundError(f"State file no encontrado: {state_name}.json")

            shutil.copy2(src_state, CURRENT)
            print(f"✅  {state_name}.json  →  current_state.json")

            # ── Leer y parsear el response file ───────────────────────────────
            src_response = os.path.join(RESPONSES_PATH, f"{response_name}.json")
            if not os.path.exists(src_response):
                raise FileNotFoundError(f"Response file no encontrado: {response_name}.json")

            with open(src_response, "r", encoding="utf-8") as f:
                response_body = extract_json_body(f.read())

            new_status = response_body.get("data", {}).get("loyaltyStatus", "—").upper()
            new_action = response_body.get("data", {}).get("action", "—").upper()
            print(f"  ┌{'─' * 85}┐")
            print(f"  │  {'BEFORE':16}  →  status = {prev_status:12} , action = {prev_action:<28} │")
            print(f"  │  {'PATH ACTION':16}  →  {action:<62}│")
            print(f"  │  {'AFTER':16}  →  status = {new_status:12} , action = {new_action:<28} │")
            print(f"  └{'─' * 85}┘")

            print(f"📤  Retornando {response_name}.json")
            self._respond(200, response_body)
            print()

        except Exception as e:
            print(f"❌  Error: {e}")
            self._respond(500, {"error": str(e)})
            print()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _respond(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type",            "application/json; charset=utf-8")
        self.send_header("Content-Length",          str(len(body)))
        self.send_header("x-correlation-id",        "66b141f0e5a34e59e4604b6ad3a50e1a")
        self.send_header("x-app-version",           "3.892.5")
        self.send_header("x-content-type-options",  "nosniff")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # silencia logs HTTP del servidor


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    server = HTTPServer(("localhost", PORT), LoyaltyHandler)
    print(f"🚀  Loyalty server corriendo en http://localhost:{PORT}")
    print(f"📁  States:    {STATES_PATH}")
    print(f"📁  Responses: {RESPONSES_PATH}")
    print(f"     Configura en Proxyman: Map Remote")
    print(f"     PATCH ...pocket-bff/users/me/loyalty/status  →  http://localhost:{PORT}/pocket-bff/users/me/loyalty/status")
    print("     Presiona Ctrl+C para detener\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑  Servidor detenido")
