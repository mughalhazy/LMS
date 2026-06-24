from __future__ import annotations

import base64, hashlib, hmac as _hmac, json, os, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Tuple
from urllib.parse import parse_qs, urlparse

_CAT_EXEMPT = {"/health", "/metrics"}
def _jwt_valid(h: str | None) -> bool:
    s = os.getenv("JWT_SHARED_SECRET")
    if not s: return True
    if not h or not h.startswith("Bearer "): return False
    tok = h[7:]
    try:
        a, p, g = tok.split(".")
        _pad = lambda x: x + "=" * ((4 - len(x) % 4) % 4)
        exp = _hmac.new(s.encode(), f"{a}.{p}".encode(), hashlib.sha256).digest()
        if not _hmac.compare_digest(exp, base64.urlsafe_b64decode(_pad(g))): return False
        pl = json.loads(base64.urlsafe_b64decode(_pad(p))); e = pl.get("exp")
        return e is None or float(e) >= time.time()
    except Exception: return False

from .service import CatalogService
from .store import InMemoryCatalogStore

# FA-024 / G-24: register event consumers at module load
from .consumers import register_consumers as _register_consumers
_register_consumers()


STORE = InMemoryCatalogStore()
SERVICE = CatalogService(STORE)


class CatalogHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        pass

    def _send(self, status: int, body: Dict[str, Any]) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-API-Version", "v1")  # CAT-004
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) if length else b"{}")

    def _qs(self, key: str) -> str | None:
        params = parse_qs(urlparse(self.path).query)
        vals = params.get(key, [])
        return vals[0] if vals else None

    def _base(self) -> str:
        return urlparse(self.path).path

    def _dispatch_get(self) -> Tuple[int, Dict[str, Any]]:
        p = self._base()
        tid = self.headers.get("X-Tenant-Id", "")

        if p == "/api/v1/catalog/products":
            return SERVICE.list_products(tid, self._qs("status"), self._qs("segment"))
        if p.startswith("/api/v1/catalog/products/") and not p.endswith("/offers"):
            pid = p.split("/api/v1/catalog/products/")[1]
            return SERVICE.get_product(pid, tid)
        if p.startswith("/api/v1/catalog/offers/"):
            oid = p.split("/api/v1/catalog/offers/")[1]
            return SERVICE.get_offer(oid)
        return 404, {"error": "not_found"}

    def _dispatch_post(self) -> Tuple[int, Dict[str, Any]]:
        p = self._base()
        body = self._read_json()
        tid = body.get("tenant_id") or self.headers.get("X-Tenant-Id", "")

        if p == "/api/v1/catalog/products":
            return SERVICE.create_product(body)
        if p.endswith("/publish"):
            pid = p.split("/api/v1/catalog/products/")[1].replace("/publish", "")
            return SERVICE.publish_product(pid, tid)
        if p.endswith("/retire"):
            pid = p.split("/api/v1/catalog/products/")[1].replace("/retire", "")
            return SERVICE.retire_product(pid, tid)
        if p.endswith("/offers"):
            pid = p.split("/api/v1/catalog/products/")[1].replace("/offers", "")
            return SERVICE.create_offer(pid, tid, body)
        if p == "/api/v1/catalog/resolve-snapshot":
            return SERVICE.resolve_snapshot(tid, body.get("product_ids", []))
        if p.startswith("/api/v1/catalog/tenants/") and p.endswith("/config"):
            tid2 = p.split("/api/v1/catalog/tenants/")[1].replace("/config", "")
            return SERVICE.update_tenant_config(tid2, body)
        return 404, {"error": "not_found"}

    def _dispatch_patch(self) -> Tuple[int, Dict[str, Any]]:
        p = self._base()
        body = self._read_json()
        tid = body.get("tenant_id") or self.headers.get("X-Tenant-Id", "")

        if p.startswith("/api/v1/catalog/products/"):
            pid = p.split("/api/v1/catalog/products/")[1]
            return SERVICE.update_product(pid, tid, body)
        return 404, {"error": "not_found"}

    def do_GET(self) -> None:  # noqa: N802
        if self._base() not in _CAT_EXEMPT and not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        if self._base() == "/health":
            self._send(200, {"status": "ok", "service": "catalog-service"}); return
        if self._base() == "/metrics":
            self._send(200, {"service": "catalog-service", "service_up": 1}); return
        try:
            self._send(*self._dispatch_get())
        except Exception as exc:
            self._send(500, {"error": str(exc)})

    def do_POST(self) -> None:  # noqa: N802
        if not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        try:
            self._send(*self._dispatch_post())
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})

    def do_PATCH(self) -> None:  # noqa: N802
        if not _jwt_valid(self.headers.get("Authorization")):
            self._send(401, {"error": "unauthorized"}); return
        try:
            self._send(*self._dispatch_patch())
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})


def run(host: str = "0.0.0.0", port: int = 8094) -> None:
    server = HTTPServer((host, port), CatalogHandler)
    print(f"Catalog service listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run()
