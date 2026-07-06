#!/usr/bin/env python3
"""MemeRadar-webserver.

Zelfde als `python3 -m http.server`, maar met een denylist zodat gevoelige
bestanden (wallet-sleutels, pid-bestanden, verborgen bestanden) nooit
geserveerd worden — ook niet als de server via wifi bereikbaar is.
"""
import http.server
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765

BLOCKED_NAMES = {"wallet.json", "bot.pid", "serve.py"}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=HERE, **kwargs)

    def _blocked(self):
        path = self.path.split("?")[0].split("#")[0]
        parts = [p for p in path.split("/") if p]
        return any(p.startswith(".") or p in BLOCKED_NAMES for p in parts)

    def send_head(self):
        if self._blocked():
            self.send_error(403, "Geblokkeerd")
            return None
        return super().send_head()

    def end_headers(self):
        # browsers moeten altijd de nieuwste versie ophalen (wel conditioneel,
        # dus snel) — voorkomt dat gebruikers oude app-versies blijven zien
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, fmt, *args):  # stil, behalve fouten
        if args and str(args[1]).startswith(("4", "5")):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"MemeRadar-server op poort {PORT} (alle interfaces, denylist actief)")
    server.serve_forever()
