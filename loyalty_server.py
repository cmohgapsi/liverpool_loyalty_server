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
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

from state_utils import load_env, log_request
from config_handler import CONFIG, VERSION, CONFIGURATION_PATH, _paths, ConfigHandlerMixin
from log_handler import LogHandlerMixin
from events_handler import EventsHandlerMixin, push_log_entry
from coupons_handler import CouponsHandlerMixin
from enroll_handler import EnrollHandlerMixin
from status_handler import StatusHandlerMixin

# ─── Configuración inmutable ──────────────────────────────────────────────────
_env           = load_env(os.path.join(os.path.dirname(__file__), ".env"))
BASE_PATH      = _env.get("BASE_PATH", os.path.dirname(__file__))
STATES_PATH    = os.path.join(BASE_PATH, "states")
RESPONSES_PATH = os.path.join(BASE_PATH, "responses")
CURRENT        = os.path.join(STATES_PATH, "current_state.json")
PORT           = int(_env.get("PORT", 9876))
LOG_PATH       = "/log"
EVENTS_PATH    = "/events"
# ─────────────────────────────────────────────────────────────────────────────


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class LoyaltyHandler(EventsHandlerMixin, ConfigHandlerMixin, LogHandlerMixin, CouponsHandlerMixin, EnrollHandlerMixin, StatusHandlerMixin, BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        p = _paths()
        if path == EVENTS_PATH:
            self._handle_get_events()
            return
        if path == CONFIGURATION_PATH:
            self._handle_get_configuration()
            return
        if path == LOG_PATH:
            self._handle_get_log()
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
        if self.path != p["status_path"]:
            self._not_found()
            return
        self._handle_patch_status(STATES_PATH, RESPONSES_PATH, CURRENT)

    def do_PUT(self):
        if self.path != CONFIGURATION_PATH:
            self._not_found()
            return
        self._handle_put_configuration()

    def do_DELETE(self):
        if self.path != LOG_PATH:
            self._not_found()
            return
        self._handle_delete_log()

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
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def _respond(self, code, payload):
        path = self.path.split("?")[0]
        delay_ms = CONFIG.get("DELAY_MS", 0)
        if (delay_ms > 0
                and path not in (LOG_PATH, CONFIGURATION_PATH)
                and self.headers.get("server_delay", "").lower() != "false"):
            time.sleep(delay_ms / 1000)

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
        if self.headers.get("server-log", "").lower() != "false":
            entry = log_request(
                self.command,
                *self.server.server_address,
                self.path,
                code,
                getattr(self, "_request_body", None),
                headers=dict(self.headers),
                response=payload,
                **getattr(self, "_log_extras", {}),
            )
            push_log_entry(entry)

    def log_message(self, *args):
        pass  # silencia logs HTTP del servidor


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    server = ThreadingHTTPServer(("localhost", PORT), LoyaltyHandler)
    p = _paths()
    print(f"🚀  Loyalty server corriendo en http://localhost:{PORT}  [v{VERSION}]")
    print(f"🗂️   Base path:  /{CONFIG['TARGET_BASE_PATH']}")
    print(f"📁  States:    {STATES_PATH}")
    print(f"📁  Responses: {RESPONSES_PATH}")
    print(f"🌐  GET    {CONFIGURATION_PATH}")
    print(f"🌐  GET    {LOG_PATH}")
    print(f"🌐  GET    {EVENTS_PATH}  (SSE — push de eventos)")
    print(f"🌐  PUT    {CONFIGURATION_PATH}")
    print(f"🌐  DELETE {LOG_PATH}")
    print(f"🌐  GET   {p['status']}")
    print(f"🌐  GET   {p['coupons']}  [suffix={CONFIG['COUPONS_LIST_SUFFIX']}]")
    print(f"🌐  GET   {p['redeemed']}  [suffix={CONFIG['COUPONS_REDEEMED_SUFFIX']}]")
    print(f"🌐  GET   {p['checkoutCoupons']}?isBuyNow=<bool>  [suffix={CONFIG['CHECKOUT_COUPONS_SUFFIX']}]")
    print(f"🌐  GET   {p['cancelReasons']}")
    print(f"🌐  POST  {p['enroll']}")
    print(f"🌐  PATCH {p['status_path']}")
    print("     Presiona Ctrl+C para detener\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑  Servidor detenido")
