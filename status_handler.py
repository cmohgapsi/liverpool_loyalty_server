import json
import os
import shutil

from state_utils import extract_json_body, extract_http_status, print_operation_result, read_current_status, resolve_response_file


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


class StatusHandlerMixin:

    def _handle_get_status(self, current: str):
        try:
            print(f"📨  GET {self.path}")
            if not os.path.exists(current):
                raise FileNotFoundError(f"current_state.json no encontrado en {current}")

            prev_status, prev_action = read_current_status(current)
            print(f"  ┌{'─' * 79}┐")
            print(f"  │  {'STATUS':10}  →  status = {prev_status:12} , action = {prev_action:<28} │")
            print(f"  └{'─' * 79}┘")

            with open(current, "r", encoding="utf-8") as f:
                raw = f.read()

            print(f"📤  Retornando current_state.json")
            self._respond(extract_http_status(raw), extract_json_body(raw))
            print()
        except Exception as e:
            print(f"❌  Error: {e}")
            self._respond(500, {"error": str(e)})
            print()

    def _handle_get_cancel_reasons(self, responses_path: str):
        try:
            print(f"📨  GET {self.path}")
            filename = "get_loyalty_cancel_reasons.json"
            src = resolve_response_file(responses_path, self.path, filename)
            if not os.path.exists(src):
                raise FileNotFoundError(f"Response file no encontrado: {filename}")
            with open(src, "r", encoding="utf-8") as f:
                raw = f.read()
            print(f"📤  Retornando {filename}")
            self._respond(extract_http_status(raw), extract_json_body(raw))
            print()
        except Exception as e:
            print(f"❌  Error: {e}")
            self._respond(500, {"error": str(e)})
            print()

    def _handle_patch_status(self, states_path: str, responses_path: str, current: str):
        try:
            length = int(self.headers.get("Content-Length", 0))
            data   = json.loads(self.rfile.read(length).decode("utf-8"))
            self._request_body = data

            action = data.get("action", "")
            value  = data.get("value")
            key    = (action, value)

            print(f"📨  PATCH {self.path} → action='{action}', value={value}")

            if action == "unenroll":
                current_status, _ = read_current_status(current)
                if current_status.upper() != "ENROLLED":
                    print(f"⚠️  409 PATCH {self.path} — unenroll rechazado, status actual: {current_status}")
                    print()
                    self._respond(409, {"status": {
                        "status": "ERROR",
                        "statusCode": 409,
                        "successMessage": "invalid operation, current membership is not enrolled"
                    }})
                    return

            if action == "unenroll" and not isinstance(data.get("cancelReason"), str):
                print(f"⚠️  400 PATCH {self.path} — campo 'cancelReason' faltante o inválido")
                print()
                self._respond(400, {"status": {
                    "status": "ERROR",
                    "statusCode": 400,
                    "successMessage": "cancelReason do not received"
                }})
                return

            if key not in SCENARIOS:
                print("⚪  Sin escenario coincidente — retornando 200 vacío")
                self._respond(200, {
                    "status": {"status": "OK", "statusCode": 0,
                               "successMessage": "No scenario matched"}
                })
                print()
                return

            state_name, response_name = SCENARIOS[key]
            prev_status, prev_action  = read_current_status(current)

            src_state = os.path.join(states_path, f"{state_name}.json")
            if not os.path.exists(src_state):
                raise FileNotFoundError(f"State file no encontrado: {state_name}.json")

            shutil.copy2(src_state, current)
            print(f"✅  {state_name}.json  →  current_state.json")

            src_response = resolve_response_file(responses_path, self.path, f"{response_name}.json")
            if not os.path.exists(src_response):
                raise FileNotFoundError(f"Response file no encontrado: {response_name}.json")

            with open(src_response, "r", encoding="utf-8") as f:
                raw_response = f.read()
            response_body = extract_json_body(raw_response)
            response_code = extract_http_status(raw_response)

            new_status = response_body.get("data", {}).get("loyaltyStatus", "—").upper()
            new_action = response_body.get("data", {}).get("action", "—").upper()
            self._request_body = data
            self._log_extras = {
                "prev_status": prev_status,
                "prev_action": prev_action,
                "operation":   "STATUS",
                "action":      action,
                "new_status":  new_status,
                "new_action":  new_action,
            }
            print_operation_result(prev_status, prev_action, "STATUS", action, new_status, new_action)

            print(f"📤  Retornando {response_name}.json")
            self._respond(response_code, response_body)
            print()

        except Exception as e:
            print(f"❌  Error: {e}")
            self._respond(500, {"error": str(e)})
            print()
