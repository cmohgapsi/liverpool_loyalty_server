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

# ─── Configuración inmutable ──────────────────────────────────────────────────
_env           = load_env(os.path.join(os.path.dirname(__file__), ".env"))
BASE_PATH      = _env.get("BASE_PATH", os.path.dirname(__file__))
STATES_PATH    = os.path.join(BASE_PATH, "states")
RESPONSES_PATH = os.path.join(BASE_PATH, "responses")
CURRENT        = os.path.join(STATES_PATH, "current_state.json")
VERSION            = _env.get("VERSION", "0.0.0")
PORT               = int(_env.get("PORT", 9876))
CONFIGURATION_PATH = "/configuration"

# ─── Configuración mutable — inicializada desde .env ─────────────────────────
# Se puede actualizar en caliente vía PUT /configuration sin reiniciar.
CONFIG = {
    "TARGET_BASE_PATH":        _env.get("TARGET_BASE_PATH",        "pocket-bff"),
    "COUPONS_LIST_SUFFIX":     _env.get("COUPONS_LIST_SUFFIX",     "empty"),
    "COUPONS_REDEEMED_SUFFIX": _env.get("COUPONS_REDEEMED_SUFFIX", "empty"),
    "CHECKOUT_COUPONS_SUFFIX": _env.get("CHECKOUT_COUPONS_SUFFIX", "cart"),
    "LOYALTY_MEMBER_ID":       _env.get("LOYALTY_MEMBER_ID",       "720100015844"),
    "USER_ID":                 int(_env.get("USER_ID",             2465729859)),
}
_CONFIGURABLE = set(CONFIG.keys())
# ─────────────────────────────────────────────────────────────────────────────


def _paths() -> dict[str, str]:
    """Computa los paths desde CONFIG['TARGET_BASE_PATH'] en cada llamada."""
    b = f"/{CONFIG['TARGET_BASE_PATH']}"
    return {
        "status":          f"{b}/users/me/loyalty/status",
        "coupons":         f"{b}/users/me/loyalty/coupons",
        "redeemed":        f"{b}/users/me/loyalty/coupons/redeemed",
        "enroll":          f"{b}/users/me/loyalty/enroll",
        "checkoutCoupons": f"{b}/checkout/coupons",
        "cancelReasons":   f"{b}/loyalty/cancel-reasons",
        "configuration":   CONFIGURATION_PATH,
    }


class LoyaltyHandler(CouponsHandlerMixin, EnrollHandlerMixin, StatusHandlerMixin, BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        p = _paths()
        if path == CONFIGURATION_PATH:
            self._handle_get_configuration()
            return
        if path == p["redeemed"]:
            self._handle_get_redeemed(RESPONSES_PATH, CONFIG["COUPONS_REDEEMED_SUFFIX"])
            return
        if path == p["coupons"]:
            self._handle_get_coupons(RESPONSES_PATH, CONFIG["COUPONS_LIST_SUFFIX"])
            return
        if path == p["checkoutCoupons"]:
            self._handle_get_checkout_coupons(RESPONSES_PATH, CONFIG["CHECKOUT_COUPONS_SUFFIX"])
            return
        if path == p["cancelReasons"]:
            self._handle_get_cancel_reasons(RESPONSES_PATH)
            return
        if path != p["status"]:
            self._not_found()
            return
        self._handle_get_status(CURRENT)

    def do_POST(self):
        p = _paths()
        if self.path != p["enroll"]:
            self._not_found()
            return
        self._handle_post_enroll(CURRENT, CONFIG["LOYALTY_MEMBER_ID"], CONFIG["USER_ID"])

    def do_PATCH(self):
        p = _paths()
        if self.path != p["status"]:
            self._not_found()
            return
        self._handle_patch_status(STATES_PATH, RESPONSES_PATH, CURRENT)

    def do_PUT(self):
        if self.path != CONFIGURATION_PATH:
            self._not_found()
            return
        self._handle_put_configuration()

    # ── Handlers propios ──────────────────────────────────────────────────────
    def _handle_get_configuration(self):
        print(f"📨  GET {self.path}")
        payload = {
            "version": VERSION,
            **CONFIG,
            "paths": _paths(),
        }
        print(f"📤  Retornando configuración del servidor")
        self._respond(200, payload)
        print()

    def _handle_put_configuration(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = json.loads(self.rfile.read(length).decode("utf-8"))

            updated = {}
            ignored = {}
            for key, value in body.items():
                if key in _CONFIGURABLE:
                    CONFIG[key] = int(value) if key == "USER_ID" else value
                    updated[key] = CONFIG[key]
                else:
                    ignored[key] = value

            print(f"🔧  PUT {self.path}")
            for k, v in updated.items():
                print(f"    {k} = {v}")
            if ignored:
                print(f"    ⚠️  ignorados (no configurables): {list(ignored.keys())}")
            print()

            self._respond(200, {
                "status": {"status": "OK", "statusCode": 0},
                "updated":       updated,
                "configuration": {"version": VERSION, **CONFIG, "paths": _paths()},
            })
        except Exception as e:
            print(f"❌  Error: {e}")
            self._respond(500, {"error": str(e)})
            print()

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
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, x-correlation-id")

    def _respond(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type",           "application/json; charset=utf-8")
        self.send_header("Content-Length",         str(len(body)))
        self.send_header("x-correlation-id",       "66b141f0e5a34e59e4604b6ad3a50e1a")
        self.send_header("x-app-version",          "3.892.5")
        self.send_header("x-content-type-options", "nosniff")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # silencia logs HTTP del servidor


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    server = HTTPServer(("localhost", PORT), LoyaltyHandler)
    p = _paths()
    print(f"🚀  Loyalty server corriendo en http://localhost:{PORT}  [v{VERSION}]")
    print(f"🗂️   Base path:  /{CONFIG['TARGET_BASE_PATH']}")
    print(f"📁  States:    {STATES_PATH}")
    print(f"📁  Responses: {RESPONSES_PATH}")
    print(f"🌐  GET   {CONFIGURATION_PATH}")
    print(f"🌐  PUT   {CONFIGURATION_PATH}")
    print(f"🌐  GET   {p['status']}")
    print(f"🌐  GET   {p['coupons']}  [suffix={CONFIG['COUPONS_LIST_SUFFIX']}]")
    print(f"🌐  GET   {p['redeemed']}  [suffix={CONFIG['COUPONS_REDEEMED_SUFFIX']}]")
    print(f"🌐  GET   {p['checkoutCoupons']}?isBuyNow=<bool>  [suffix={CONFIG['CHECKOUT_COUPONS_SUFFIX']}]")
    print(f"🌐  GET   {p['cancelReasons']}")
    print(f"🌐  POST  {p['enroll']}")
    print(f"🌐  PATCH {p['status']}")
    print("     Presiona Ctrl+C para detener\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑  Servidor detenido")
