"""The console's web service: the standard library only, for one reader on this machine.

    python -m console.server            # http://127.0.0.1:8770

It listens on this machine only unless ``--host`` says otherwise (the container of
console/compose.yaml listens inside itself and Docker publishes the port on the addresses
named there). There is no password: whoever can reach the port can read the repository's
reports and add requests. It reads the repository on every request, writes only the
owner's requests, the news inbox and the exploration log under research/, and runs model
code only through the fixed questions of console/sim.py.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from console import catalog, sim

STATIC = catalog.ROOT / "console" / "static"
SERVED = ("docs", "reports", "research", "snapshots")
SUFFIXES = {".html", ".md", ".png", ".json", ".jsonl", ".log", ".svg", ".txt"}


def get(path: str, query: dict) -> object:
    one = lambda k, d="": query.get(k, [d])[0]  # noqa: E731
    if path == "/api/overview":
        return catalog.overview()
    if path == "/api/model":
        return catalog.describe(one("version", "v0.3"), json.loads(one("knobs", "{}")))
    if path == "/api/claims":
        return catalog.claims(one("version", "v0.3"))
    if path == "/api/runs":
        return catalog.runs()
    if path == "/api/states":
        return catalog.states()
    if path == "/api/evidence":
        return catalog.evidence()
    if path == "/api/glossary":
        return catalog.glossary()[1]
    if path.startswith("/api/store/"):
        name = path.rsplit("/", 1)[1]
        if name in ("requests", "news", "findings"):
            return catalog.store(name)
    raise KeyError(path)


def post(path: str, body: dict) -> object:
    if path == "/api/sim/begin":
        return sim.begin(body)
    if path == "/api/sim/step":
        return sim.step(body)
    if path == "/api/sim/shortest":
        return sim.shortest(body)
    if path == "/api/queue/move":
        return catalog.move(str(body.get("id")), str(body.get("to")))
    if path in ("/api/store/requests", "/api/store/news"):
        return catalog.store_write(path.rsplit("/", 1)[1], body)
    raise KeyError(path)


class Handler(BaseHTTPRequestHandler):
    server_version = "wavefront-console"

    def log_message(self, *args) -> None:  # quiet
        pass

    def _send(self, code: int, body: bytes, kind: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, fn) -> None:
        try:
            self._send(200, json.dumps(fn(), ensure_ascii=False).encode(), "application/json")
        except KeyError:
            self._send(404, b'{"error": "not found"}', "application/json")
        except Exception as exc:  # shown to the reader, who is the owner
            body = json.dumps({"error": f"{type(exc).__name__}: {exc}"}).encode()
            self._send(400, body, "application/json")

    def _file(self, path) -> None:
        path = path.resolve()
        if not path.is_file() or path.suffix not in SUFFIXES | {".js", ".css"}:
            self._send(404, b"not found", "text/plain")
            return
        kind = mimetypes.guess_type(path.name)[0] or "text/plain"
        if path.suffix in (".md", ".jsonl", ".log"):
            kind = "text/plain"
        if kind.startswith("text/") or kind.endswith(("json", "javascript")):
            kind += "; charset=utf-8"
        body = path.read_bytes()
        if path.name == "index.html":
            # The page's script and style carry their modification time, so that a browser
            # which keeps old copies (phones do) still loads the current ones.
            for name in ("app.js", "style.css"):
                stamp = int((STATIC / name).stat().st_mtime)
                body = body.replace(f'"{name}"'.encode(), f'"{name}?v={stamp}"'.encode())
            body = body.replace(
                b"</body>", f"<script>window.BUILD={stamp}</script></body>".encode()
            )
        self._send(200, body, kind)

    def do_GET(self) -> None:
        url = urlparse(self.path)
        if url.path.startswith("/api/"):
            self._json(lambda: get(url.path, parse_qs(url.query)))
        elif url.path == "/hold":
            # Keeps a page's load event open while its data arrives (for screenshots).
            time.sleep(min(5.0, float(parse_qs(url.query).get("ms", ["0"])[0]) / 1000))
            self._send(204, b"", "text/plain")
        elif url.path.startswith("/file/"):
            rel = url.path[6:]
            target = (catalog.ROOT / rel).resolve()
            inside = any(target.is_relative_to(catalog.ROOT / d) for d in SERVED)
            self._file(target) if inside else self._send(404, b"not found", "text/plain")
        else:
            name = "index.html" if url.path in ("/", "") else url.path.lstrip("/")
            target = (STATIC / name).resolve()
            ok = target.is_relative_to(STATIC)
            self._file(target) if ok else self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        if length > 200_000:
            self._send(413, b"too large", "text/plain")
            return
        raw = self.rfile.read(length) or b"{}"
        self._json(lambda: post(urlparse(self.path).path, json.loads(raw)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8770)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"wave_front console on http://{args.host}:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
