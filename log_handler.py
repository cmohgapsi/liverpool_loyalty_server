import json
import os

from state_utils import LOG_FILE


class LogHandlerMixin:

    def _handle_get_log(self):
        print(f"📨  GET {self.path}")
        try:
            if not os.path.exists(LOG_FILE):
                entries = []
            else:
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    entries = [json.loads(line) for line in f if line.strip()]
            entries.reverse()
            print(f"📤  Retornando {len(entries)} entradas del log")
            self._respond(200, entries)
            print()
        except Exception as e:
            print(f"❌  Error: {e}")
            self._respond(500, {"error": str(e)})
            print()

    def _handle_delete_log(self):
        print(f"🗑️   DELETE {self.path}")
        open(LOG_FILE, "w").close()
        print(f"✅  server.log vaciado")
        print()
        self._respond(200, {"status": {"status": "OK", "statusCode": 0, "successMessage": "Log cleared"}})
