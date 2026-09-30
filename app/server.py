"""Небольшой веб-сервер на стандартной библиотеке.

Отдаёт статику из static/ и немного JSON:
    /            — главная страница
    /api/health  — {"status": "ok"}
    /api/info    — hostname, порт, версия, uptime, счётчик запросов

Порт берётся из переменной окружения PORT (по умолчанию 8000).
"""

from __future__ import annotations

import json
import os
import signal
import socket
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))
APP_VERSION = os.environ.get("APP_VERSION", "dev")
APP_NAME = os.environ.get("APP_NAME", "Docker Hello App")
STATIC_DIR = os.environ.get("STATIC_DIR", str(Path(__file__).parent / "static"))

STARTED_AT = time.monotonic()
REQUESTS_SERVED = 0


class AppHandler(SimpleHTTPRequestHandler):
    server_version = f"{APP_NAME}/{APP_VERSION}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        global REQUESTS_SERVED
        REQUESTS_SERVED += 1

        path = self.path.split("?", 1)[0].rstrip("/") or "/"

        if path == "/api/health":
            self.send_json({"status": "ok"})
        elif path == "/api/info":
            self.send_json(
                {
                    "app": APP_NAME,
                    "version": APP_VERSION,
                    "port": PORT,
                    "hostname": socket.gethostname(),
                    "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "uptime_seconds": round(time.monotonic() - STARTED_AT, 1),
                    "requests_served": REQUESTS_SERVED,
                    "python": sys.version.split()[0],
                }
            )
        else:
            super().do_GET()

    def send_json(self, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        sys.stderr.write(f"[{stamp}] {self.address_string()} {fmt % args}\n")
        sys.stderr.flush()


def healthcheck() -> int:
    try:
        with urlopen(f"http://127.0.0.1:{PORT}/api/health", timeout=2) as response:
            return 0 if response.status == 200 else 1
    except Exception:
        return 1


def main() -> int:
    if "--healthcheck" in sys.argv:
        return healthcheck()

    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    server.daemon_threads = True

    stop_event = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())
    signal.signal(signal.SIGINT, lambda *_: stop_event.set())

    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()

    print(f"{APP_NAME} v{APP_VERSION} слушает http://{HOST}:{PORT}", flush=True)
    print(f"Статика: {STATIC_DIR}", flush=True)

    stop_event.wait()

    print("Останавливаю сервер...", flush=True)
    server.shutdown()
    worker.join(timeout=5)
    server.server_close()
    print("Сервер остановлен.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
