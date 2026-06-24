from __future__ import annotations

from fastapi import FastAPI, HTTPException, Depends
from .security import apply_security_headers, require_jwt

from app.models import CallbackRequest, InitiateSSORequest
from app.service import SSOService

app = FastAPI(title="sso-service", version="0.1.0", dependencies=[Depends(require_jwt)])


# CAT-004: api-versioning-strategy.md §1 — X-API-Version header required on every response
@app.middleware("http")
async def _add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response


# FA-024 / G-24: register event consumers on startup
from .consumers import register_consumers as _register_consumers
_register_consumers()


apply_security_headers(app)
service = SSOService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "sso-service"}


@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "sso-service", "service_up": 1}


@app.get("/api/v1/sso/providers")
def providers() -> dict[str, dict[str, str]]:
    return {"providers_supported": service.provider_matrix()}


@app.post("/api/v1/sso/initiate")
def initiate_sso(req: InitiateSSORequest):
    try:
        return service.initiate(req)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/sso/callback")
def callback(req: CallbackRequest):
    try:
        return service.callback(req)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
