import json
import queue
import threading


_clients: list[queue.Queue] = []
_clients_lock = threading.Lock()


def push_log_entry(entry: dict):
    """Difunde un log entry a todos los clientes SSE conectados."""
    if not _clients:
        return

    path   = entry.get("path", "")
    method = entry.get("method", "")

    # GET /log: el cliente está leyendo su propio log, no notificar
    if method == "GET" and path == "/log":
        return

    # DELETE /log: notificar a los clientes que deben limpiar su vista
    if method == "DELETE" and path == "/log":
        _broadcast("event: log-cleared\ndata: {}\n\n")
        return

    _broadcast(f"event: log-entry\ndata: {json.dumps(entry, ensure_ascii=False)}\n\n")


def _broadcast(message: str):
    encoded = message.encode("utf-8")
    with _clients_lock:
        for q in list(_clients):
            try:
                q.put_nowait(encoded)
            except Exception:
                pass


class EventsHandlerMixin:

    def _handle_get_events(self):
        self.send_response(200)
        self.send_header("Content-Type",  "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection",    "keep-alive")
        self._send_cors_headers()
        self.end_headers()

        q: queue.Queue = queue.Queue()
        with _clients_lock:
            _clients.append(q)
        n = len(_clients)
        print(f"📡  SSE client conectado  ({n} activo{'s' if n != 1 else ''})")

        try:
            while True:
                try:
                    msg = q.get(timeout=20)
                    self.wfile.write(msg)
                    self.wfile.flush()
                except queue.Empty:
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
        except Exception:
            pass
        finally:
            with _clients_lock:
                if q in _clients:
                    _clients.remove(q)
            n = len(_clients)
            print(f"📡  SSE client desconectado ({n} activo{'s' if n != 1 else ''})")
