import json
import os
import shutil

from state_utils import extract_json_body, print_operation_result, read_current_status


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
                body = extract_json_body(f.read())

            print(f"📤  Retornando current_state.json")
            self._respond(200, body)
            print()
        except Exception as e:
            print(f"❌  Error: {e}")
            self._respond(500, {"error": str(e)})
            print()

    def _handle_get_cancel_reasons(self, responses_path: str):
        try:
            print(f"📨  GET {self.path}")
            filename = "get_loyalty_cancel_reasons.json"
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

    def _handle_patch_status(self, states_path: str, responses_path: str, current: str):
        try:
            length = int(self.headers.get("Content-Length", 0))
            data   = json.loads(self.rfile.read(length).decode("utf-8"))

            action = data.get("action", "")
            value  = data.get("value")
            key    = (action, value)

            print(f"📨  PATCH {self.path} → action='{action}', value={value}")

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

            src_response = os.path.join(responses_path, f"{response_name}.json")
            if not os.path.exists(src_response):
                raise FileNotFoundError(f"Response file no encontrado: {response_name}.json")

            with open(src_response, "r", encoding="utf-8") as f:
                response_body = extract_json_body(f.read())

            new_status = response_body.get("data", {}).get("loyaltyStatus", "—").upper()
            new_action = response_body.get("data", {}).get("action", "—").upper()
            print_operation_result(prev_status, prev_action, "STATUS", action, new_status, new_action)

            print(f"📤  Retornando {response_name}.json")
            self._respond(200, response_body)
            print()

        except Exception as e:
            print(f"❌  Error: {e}")
            self._respond(500, {"error": str(e)})
            print()
