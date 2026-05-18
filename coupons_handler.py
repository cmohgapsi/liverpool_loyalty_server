import os
from urllib.parse import parse_qs, urlparse

from state_utils import extract_json_body


class CouponsHandlerMixin:

    def _handle_get_redeemed(self, responses_path: str, suffix: str):
        try:
            print(f"📨  GET {self.path}  [suffix={suffix}]")
            filename = f"get_loyalty_coupons_redeemed_{suffix}.json"
            src = os.path.join(responses_path, filename)
            if not os.path.exists(src):
                raise FileNotFoundError(f"Response file no encontrado: {filename}")
            with open(src, "r", encoding="utf-8") as f:
                body = extract_json_body(f.read())
            print(f"📤  Retornando {filename}")
            self._respond(200, body)
            print()
        except Exception as e:
            print(f"❌  Error: {e}")
            self._respond(500, {"error": str(e)})
            print()

    def _handle_get_coupons(self, responses_path: str, suffix: str):
        try:
            print(f"📨  GET {self.path}  [suffix={suffix}]")
            filename = f"get_loyalty_coupons_enrolled_{suffix}.json"
            src = os.path.join(responses_path, filename)
            if not os.path.exists(src):
                raise FileNotFoundError(f"Response file no encontrado: {filename}")
            with open(src, "r", encoding="utf-8") as f:
                body = extract_json_body(f.read())
            print(f"📤  Retornando {filename}")
            self._respond(200, body)
            print()
        except Exception as e:
            print(f"❌  Error: {e}")
            self._respond(500, {"error": str(e)})
            print()

    def _handle_get_checkout_coupons(self, responses_path: str, suffix: str):
        try:
            params = parse_qs(urlparse(self.path).query)

            if "isBuyNow" not in params:
                print(f"⚠️  400 GET {self.path} — parámetro 'isBuyNow' faltante")
                print()
                self._respond(400, {"status": {
                    "status": "ERROR",
                    "statusCode": 400,
                    "successMessage": "Missing required parameter: isBuyNow"
                }})
                return

            is_buy_now = params["isBuyNow"][0].lower()
            print(f"📨  GET {self.path}  [isBuyNow={is_buy_now}]  [suffix={suffix}]")
            filename = f"get_checkout_coupons_{suffix}.json"
            src = os.path.join(responses_path, filename)
            if not os.path.exists(src):
                raise FileNotFoundError(f"Response file no encontrado: {filename}")
            with open(src, "r", encoding="utf-8") as f:
                body = extract_json_body(f.read())
            print(f"📤  Retornando {filename}")
            self._respond(200, body)
            print()
        except Exception as e:
            print(f"❌  Error: {e}")
            self._respond(500, {"error": str(e)})
            print()
