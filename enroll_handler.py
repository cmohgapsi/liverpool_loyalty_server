import json
import os
from datetime import date

from state_utils import extract_json_body

ENROLL_REQUIRED_FIELDS = {"firstName", "lastName", "motherLastName", "gender", "dateOfBirth"}


class EnrollHandlerMixin:

    def _handle_post_enroll(self, current: str, loyalty_member_id: str, user_id: int):
        try:
            if not os.path.exists(current):
                raise FileNotFoundError(f"current_state.json no encontrado en {current}")

            with open(current, "r", encoding="utf-8") as f:
                state_data = extract_json_body(f.read())

            loyalty_status = state_data.get("loyaltyData", {}).get("status", "")

            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}

            print(f"📨  POST {self.path}  [loyaltyStatus={loyalty_status}]")

            if loyalty_status in ("notEnrolled", "declined"):
                self._enroll_not_enrolled(body, current, loyalty_member_id, user_id)

            elif loyalty_status == "unenrolled":
                self._enroll_unenrolled(body, current, loyalty_member_id, user_id)

            else:
                print(f"⚠️  Estado inválido para enroll: {loyalty_status}")
                self._respond(409, {"status": {
                    "status": "ERROR",
                    "statusCode": 409,
                    "successMessage": f"invalid operation, current membership {loyalty_status}"
                }})
                print()

        except Exception as e:
            print(f"❌  Error: {e}")
            self._respond(500, {"error": str(e)})
            print()

    # ── Casos ────────────────────────────────────────────────────────────────

    def _enroll_not_enrolled(self, body: dict, current: str,
                             loyalty_member_id: str, user_id: int):
        missing = ENROLL_REQUIRED_FIELDS - set(body.keys())
        if missing:
            print(f"⚠️  Faltan campos requeridos: {missing}")
            self._respond(400, {"status": {
                "status": "ERROR",
                "statusCode": 400,
                "successMessage": "Update data not received"
            }})
            print()
            return

        _update_current_state(current, body)
        print(f"✅  current_state.json actualizado → enrolled / displayWelcomeModal")

        self._respond(200, {
            "status": {"status": "OK", "statusCode": 0},
            "data": _build_enroll_response(loyalty_member_id, user_id)
        })
        print()

    def _enroll_unenrolled(self, body: dict, current: str,
                           loyalty_member_id: str, user_id: int):
        if body:
            print(f"⚠️  Body no vacío")
            self._respond(400, {"status": {
                "status": "ERROR",
                "statusCode": 400,
                "successMessage": "Body is not empty"
            }})
            print()
            return

        _update_loyalty_data(current)
        print(f"✅  current_state.json actualizado → enrolled / displayWelcomeModal")

        self._respond(200, {
            "status": {"status": "OK", "statusCode": 0},
            "data": _build_enroll_response(loyalty_member_id, user_id)
        })
        print()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_enroll_response(loyalty_member_id: str, user_id: int) -> dict:
    return {
        "loyaltyMemberId": loyalty_member_id,
        "userId":          user_id,
        "action":          "displayWelcomeModal",
        "loyaltyStatus":   "enrolled",
        "memberSince":     date.today().strftime("%Y-%m-%d"),
    }


def _update_loyalty_data(current: str):
    """Actualiza solo loyaltyData en current_state.json preservando headers HTTP raw."""
    _patch_state_file(current, lambda _: None)


def _update_current_state(current: str, body: dict):
    """Actualiza campos de usuario y loyaltyData en current_state.json
    preservando los headers HTTP raw del archivo."""
    def apply(state):
        state["firstName"]    = body["firstName"]
        state["lastName"]     = body["lastName"]
        state["maternalName"] = body["motherLastName"]
        state["dateOfBirth"]  = body["dateOfBirth"]

    _patch_state_file(current, apply)


def _patch_state_file(current: str, apply_extra):
    """Lee current_state.json, aplica cambios de loyaltyData + apply_extra y reescribe."""
    with open(current, "r", encoding="utf-8") as f:
        raw = f.read()

    separator = None
    for sep in ("\r\n\r\n", "\n\n"):
        if sep in raw:
            separator = sep
            break

    if separator:
        headers_part, json_part = raw.split(separator, 1)
        state = json.loads(json_part.strip())
    else:
        headers_part = None
        state = json.loads(raw.strip())

    state.setdefault("loyaltyData", {})
    state["loyaltyData"]["action"]      = "displayWelcomeModal"
    state["loyaltyData"]["status"]      = "enrolled"
    state["loyaltyData"]["memberSince"] = date.today().strftime("%Y-%m-%d")
    apply_extra(state)

    updated_json = json.dumps(state, ensure_ascii=False, indent=2)

    with open(current, "w", encoding="utf-8") as f:
        if headers_part is not None:
            f.write(headers_part + separator + updated_json + "\n")
        else:
            f.write(updated_json + "\n")
