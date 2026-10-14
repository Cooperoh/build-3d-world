"""Loopback-only launcher and durable data cache for the saved Rokehan page."""
from __future__ import annotations
import argparse
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import secrets
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent
APP = ROOT / "app"
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)
STATE = CACHE / "server.json"
ORIGIN = "https://tools.oyasumi-gamedev.com/rokehan/"
START = "/?lang=zh-Hans&overpass=0#ll=39.918037%2C116.389861&s=1000&season=spring&far=2"
HOSTS = {"tools.oyasumi-gamedev.com", "tiles.openfreemap.org", "s3.amazonaws.com", "cyberjapandata.gsi.go.jp", "nominatim.openstreetmap.org"}
APP_ID = "rokehan-local-20261014"
LOCKS: dict[str, threading.Lock] = {}
LOCK_GUARD = threading.Lock()

def allowed(url):
    p = urllib.parse.urlsplit(url)
    return p.scheme == "https" and p.hostname in HOSTS and not p.username and not p.password and p.port in (None, 443) and (p.hostname != "tools.oyasumi-gamedev.com" or p.path.startswith("/rokehan/"))

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed(newurl):
            raise ValueError("Redirect outside the original data sources")
        return super().redirect_request(req, fp, code, msg, headers, newurl)

OPENER = urllib.request.build_opener(SafeRedirect())

def cached_fetch(url):
    if not allowed(url):
        return 403, "text/plain", b"Data source is not permitted"
    key = hashlib.sha256(url.encode()).hexdigest()
    folder = CACHE / "http" / key[:2]
    body, meta = folder / (key + ".bin"), folder / (key + ".json")
    with LOCK_GUARD:
        lock = LOCKS.setdefault(key, threading.Lock())
    with lock:
        if body.exists() and meta.exists():
            m = json.loads(meta.read_text("utf-8"))
            return m["status"], m["type"], body.read_bytes()
        if (CACHE / "offline.flag").exists():
            with (CACHE / "offline-misses.log").open("a", encoding="utf-8") as f:
                f.write(url + "\n")
            return 503, "text/plain", b"Offline: this resource has not been saved"
        req = urllib.request.Request(url, headers={"User-Agent": "RokehanLocalArchive/1.0 (personal local copy)", "Accept-Encoding": "identity"})
        try:
            with OPENER.open(req, timeout=25) as r:
                data, status, ctype = r.read(), r.status, r.headers.get("Content-Type", "application/octet-stream")
        except urllib.error.HTTPError as e:
            if e.code != 404:
                return e.code, "text/plain", str(e).encode()
            data, status, ctype = e.read(), 404, "application/octet-stream"
        except Exception as e:
            return 502, "text/plain", str(e).encode()
        folder.mkdir(parents=True, exist_ok=True)
        body.write_bytes(data)
        meta.write_text(json.dumps({"url": url, "status": status, "type": ctype, "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}, ensure_ascii=False, indent=2), "utf-8")
        return status, ctype, data

def running():
    try:
        s = json.loads(STATE.read_text("utf-8"))
        with urllib.request.urlopen(f"http://127.0.0.1:{s['port']}/__status", timeout=1) as r:
            live = json.load(r)
        return s if live.get("app") == APP_ID and live.get("instance") == s.get("instance") else None
    except Exception:
        return None

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(APP), **kwargs)

    def log_message(self, fmt, *args):
        with (CACHE / "server.log").open("a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + (fmt % args) + "\n")

    def local_host(self):
        return self.headers.get("Host") in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

    def reply(self, status, ctype, data):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        if not self.local_host():
            return self.reply(403, "text/plain", b"Loopback host required")
        p = urllib.parse.urlsplit(self.path)
        path = urllib.parse.unquote(p.path)
        if path == "/__status":
            return self.reply(200, "application/json", json.dumps({"app": APP_ID, "instance": self.server.instance, "offline": (CACHE / "offline.flag").exists()}).encode())
        if path == "/__proxy":
            url = urllib.parse.parse_qs(p.query).get("url", [""])[0]
            return self.reply(*cached_fetch(url))
        if path == "/local-cache.js":
            return self.reply(200, "text/javascript; charset=utf-8", (ROOT / "local-cache.js").read_bytes())
        if path in ("/", "/index.html"):
            data = (APP / "index.html").read_bytes().replace(b"<head>", b'<head>\n<script src="/local-cache.js"></script>', 1)
            return self.reply(200, "text/html; charset=utf-8", data)
        target = (APP / path.lstrip("/")).resolve()
        if not target.is_relative_to(APP.resolve()):
            return self.reply(403, "text/plain", b"Invalid path")
        if target.is_file():
            return self.reply(200, mimetypes.guess_type(target.name)[0] or "application/octet-stream", target.read_bytes())
        if path.startswith(("/packs/", "/search/")):
            return self.reply(*cached_fetch(ORIGIN + path.lstrip("/") + (("?" + p.query) if p.query else "")))
        return self.reply(404, "text/plain", b"Not found")

    def do_POST(self):
        if self.local_host() and self.path == "/__stop" and secrets.compare_digest(self.headers.get("X-Local-Key", ""), self.server.secret):
            self.reply(200, "text/plain", b"Stopped")
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        else:
            self.reply(403, "text/plain", b"Not permitted")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--stop", action="store_true")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--online", action="store_true")
    args = ap.parse_args()
    if args.offline:
        (CACHE / "offline.flag").touch()
    if args.online:
        (CACHE / "offline.flag").unlink(missing_ok=True)
    live = running()
    if args.stop:
        if live:
            req = urllib.request.Request(f"http://127.0.0.1:{live['port']}/__stop", data=b"", headers={"X-Local-Key": live["secret"]}, method="POST")
            urllib.request.urlopen(req, timeout=3).close()
        return
    if live:
        if args.open:
            webbrowser.open(f"http://127.0.0.1:{live['port']}" + START)
        return
    for port in range(18764, 18785):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            continue
    else:
        raise RuntimeError("No free loopback port from 18764 to 18784")
    server.instance, server.secret = secrets.token_hex(12), secrets.token_hex(24)
    STATE.write_text(json.dumps({"port": port, "pid": os.getpid(), "instance": server.instance, "secret": server.secret}), "utf-8")
    if args.open:
        threading.Timer(0.4, lambda: webbrowser.open(f"http://127.0.0.1:{port}" + START)).start()
    try:
        server.serve_forever()
    finally:
        server.server_close()
        if STATE.exists() and json.loads(STATE.read_text("utf-8")).get("instance") == server.instance:
            STATE.unlink()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        (CACHE / "startup-error.log").write_text(traceback.format_exc(), "utf-8")
        raise
