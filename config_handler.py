import json
import os

from state_utils import load_env

_env = load_env(os.path.join(os.path.dirname(__file__), ".env"))

VERSION = _env.get("VERSION", "0.0.0")
PORT    = int(_env.get("PORT", 9876))

CONFIG = {
    "TARGET_BASE_PATH":        _env.get("TARGET_BASE_PATH",        "pocket-bff"),
    "COUPONS_LIST_SUFFIX":     _env.get("COUPONS_LIST_SUFFIX",     "empty"),
    "COUPONS_REDEEMED_SUFFIX": _env.get("COUPONS_REDEEMED_SUFFIX", "empty"),
    "CHECKOUT_COUPONS_SUFFIX": _env.get("CHECKOUT_COUPONS_SUFFIX", "cart"),
    "LOYALTY_MEMBER_ID":       _env.get("LOYALTY_MEMBER_ID",       "720100015844"),
    "USER_ID":                 int(_env.get("USER_ID",             2465729859)),
}
_CONFIGURABLE = set(CONFIG.keys())

CONFIGURATION_PATH = "/configuration"


def _paths() -> dict[str, str]:
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


class ConfigHandlerMixin:

    def _handle_get_configuration(self):
        print(f"📨  GET {self.path}")
        payload = {
            "version": VERSION,
            "PORT": PORT,
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
            self._request_body = body

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
                "configuration": {"version": VERSION, "PORT": PORT, **CONFIG, "paths": _paths()},
            })
        except Exception as e:
            print(f"❌  Error: {e}")
            self._respond(500, {"error": str(e)})
            print()
