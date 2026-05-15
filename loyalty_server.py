#!/usr/bin/env python3
"""
Proxyman State Server — Lealtad
Recibe las llamadas redirigidas por Map Remote de Proxyman y delega
en los handlers especializados de status y cupones.

Uso:
    python3 loyalty_server.py
"""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

from state_utils import load_env
from coupons_handler import CouponsHandlerMixin
from status_handler import StatusHandlerMixin

# ─── Configuración ────────────────────────────────────────────────────────────
_env = load_env(os.path.join(os.path.dirname(__file__), ".env"))
BASE_PATH      = _env.get("BASE_PATH", os.path.dirname(__file__))
STATES_PATH    = os.path.join(BASE_PATH, "states")
RESPONSES_PATH = os.path.join(BASE_PATH, "responses")
CURRENT        = os.path.join(STATES_PATH, "current_state.json")
PORT                = int(_env.get("PORT", 9876))
COUPONS_LIST_SUFFIX = _env.get("COUPONS_LIST_SUFFIX", "empty")
TARGET_PATH         = _env.get("TARGET_PATH",         "/pocket-bff/users/me/loyalty/status")
TARGET_COUPONS_PATH = _env.get("TARGET_COUPONS_PATH", "/pocket-bff/loyalty/coupons")
# ─────────────────────────────────────────────────────────────────────────────


class LoyaltyHandler(CouponsHandlerMixin, StatusHandlerMixin, BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == TARGET_COUPONS_PATH:
            self._handle_get_coupons(RESPONSES_PATH, COUPONS_LIST_SUFFIX)
            return
        if self.path != TARGET_PATH:
            self._not_found()
            return
        self._handle_get_status(CURRENT)

    def do_PATCH(self):
        if self.path != TARGET_PATH:
            self._not_found()
            return
        self._handle_patch_status(STATES_PATH, RESPONSES_PATH, CURRENT)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _not_found(self):
        print(f"🔴  404 {self.command} {self.path}")
        print()
        self._respond(404, {"status": {
            "status": f"NOT FOUND: {self.command} - {self.path}",
            "statusCode": 404
        }})

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, x-correlation-id")

    def _respond(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type",            "application/json; charset=utf-8")
        self.send_header("Content-Length",          str(len(body)))
        self.send_header("x-correlation-id",        "66b141f0e5a34e59e4604b6ad3a50e1a")
        self.send_header("x-app-version",           "3.892.5")
        self.send_header("x-content-type-options",  "nosniff")
        self._send_cors_headers()
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
    print(f"🌐  TARGET_PATH         = {TARGET_PATH}")
    print(f"🌐  TARGET_COUPONS_PATH = {TARGET_COUPONS_PATH}")
    print(f"     Configura en Proxyman: Map Remote")
    print(f"     ANY ...pocket-bff/users/me/loyalty/*  →  http://localhost:{PORT}/pocket-bff/users/me/loyalty/*")
    print("     Presiona Ctrl+C para detener\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑  Servidor detenido")
