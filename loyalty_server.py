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
from enroll_handler import EnrollHandlerMixin
from status_handler import StatusHandlerMixin

# ─── Configuración ────────────────────────────────────────────────────────────
_env = load_env(os.path.join(os.path.dirname(__file__), ".env"))
BASE_PATH      = _env.get("BASE_PATH", os.path.dirname(__file__))
STATES_PATH    = os.path.join(BASE_PATH, "states")
RESPONSES_PATH = os.path.join(BASE_PATH, "responses")
CURRENT        = os.path.join(STATES_PATH, "current_state.json")
PORT                    = int(_env.get("PORT", 9876))
TARGET_BASE_PATH        = _env.get("TARGET_BASE_PATH", "pocket-bff")
_base                   = f"/{TARGET_BASE_PATH}"
COUPONS_LIST_SUFFIX     = _env.get("COUPONS_LIST_SUFFIX",     "empty")
COUPONS_REDEEMED_SUFFIX = _env.get("COUPONS_REDEEMED_SUFFIX", "empty")
LOYALTY_MEMBER_ID       = _env.get("LOYALTY_MEMBER_ID",       "720100015844")
USER_ID                 = int(_env.get("USER_ID",              2465729859))
CHECKOUT_COUPONS_SUFFIX = _env.get("CHECKOUT_COUPONS_SUFFIX", "cart")

TARGET_PATH                  = f"{_base}/users/me/loyalty/status"
TARGET_COUPONS_PATH          = f"{_base}/users/me/loyalty/coupons"
TARGET_REDEEMED_PATH         = f"{_base}/users/me/loyalty/coupons/redeemed"
TARGET_ENROLL_PATH           = f"{_base}/users/me/loyalty/enroll"
TARGET_CHECKOUT_COUPONS_PATH = f"{_base}/checkout/coupons"
TARGET_CANCEL_REASONS_PATH   = f"{_base}/loyalty/cancel-reasons"
# ─────────────────────────────────────────────────────────────────────────────


class LoyaltyHandler(CouponsHandlerMixin, EnrollHandlerMixin, StatusHandlerMixin, BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == TARGET_REDEEMED_PATH:
            self._handle_get_redeemed(RESPONSES_PATH, COUPONS_REDEEMED_SUFFIX)
            return
        if path == TARGET_COUPONS_PATH:
            self._handle_get_coupons(RESPONSES_PATH, COUPONS_LIST_SUFFIX)
            return
        if path == TARGET_CHECKOUT_COUPONS_PATH:
            self._handle_get_checkout_coupons(RESPONSES_PATH, CHECKOUT_COUPONS_SUFFIX)
            return
        if path == TARGET_CANCEL_REASONS_PATH:
            self._handle_get_cancel_reasons(RESPONSES_PATH)
            return
        if path != TARGET_PATH:
            self._not_found()
            return
        self._handle_get_status(CURRENT)

    def do_POST(self):
        if self.path != TARGET_ENROLL_PATH:
            self._not_found()
            return
        self._handle_post_enroll(CURRENT, LOYALTY_MEMBER_ID, USER_ID)

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
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
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
    print(f"🗂️   Base path:  {_base}")
    print(f"📁  States:    {STATES_PATH}")
    print(f"📁  Responses: {RESPONSES_PATH}")
    print(f"🌐  GET  {TARGET_PATH}")
    print(f"🌐  GET  {TARGET_COUPONS_PATH}  [suffix={COUPONS_LIST_SUFFIX}]")
    print(f"🌐  GET  {TARGET_REDEEMED_PATH}  [suffix={COUPONS_REDEEMED_SUFFIX}]")
    print(f"🌐  GET  {TARGET_CHECKOUT_COUPONS_PATH}?isBuyNow=<bool>  [suffix={CHECKOUT_COUPONS_SUFFIX}]")
    print(f"🌐  GET  {TARGET_CANCEL_REASONS_PATH}")
    print(f"🌐  POST  {TARGET_ENROLL_PATH}")
    print(f"🌐  PATCH {TARGET_PATH}")
    print("     Presiona Ctrl+C para detener\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑  Servidor detenido")
