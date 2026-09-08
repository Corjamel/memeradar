#!/usr/bin/env python3
"""MemeRadar-webserver.

Serveert ALLEEN een vaste witte lijst van app-bestanden. Alles daarbuiten wordt
geweigerd — ongeacht percent-encoding (%2e), hoofdletters of pad-trucs. Zo kan
nooit de .git-map, een wallet-sleutel of broncode-historie lekken, ook niet als
de server via wifi bereikbaar is.
"""
import http.server
import os
import sys
import posixpath
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765

# exacte bestanden die de app nodig heeft
ALLOW_EXACT = {
    "", "index.html", "app.js", "swap.js", "style.css",
    "sw.js", "manifest.webmanifest", "bot/status.json",
}
# mappen waaruit alles geserveerd mag worden (statische assets)
ALLOW_PREFIX = ("vendor/", "icons/")


def _decoded_rel(path):
    """Decodeer en normaliseer het pad zoals de bestandslaag het uiteindelijk ziet."""
    path = path.split("?", 1)[0].split("#", 1)[0]
    path = urllib.parse.unquote(path, errors="surrogatepass")
    path = posixpath.normpath(path)          # collapse .. en //
    return path.lstrip("/")


def _allowed(rel):
    if rel in ALLOW_EXACT:
        return True
    return any(rel.startswith(p) for p in ALLOW_PREFIX) and ".." not in rel


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=HERE, **kwargs)

    def send_head(self):
        rel = _decoded_rel(self.path)
        parts = [p for p in rel.split("/") if p]
        # geen verborgen bestanden/mappen (.git, .env, …) en alleen de witte lijst
        if any(p.startswith(".") for p in parts) or not _allowed(rel):
            self.send_error(403, "Geblokkeerd")
            return None
        return super().send_head()

    def end_headers(self):
        # browsers altijd de nieuwste versie laten controleren
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, fmt, *args):  # stil, behalve fouten
        if args and str(args[1]).startswith(("4", "5")):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"MemeRadar-server op poort {PORT} (witte lijst actief)")
    server.serve_forever()
