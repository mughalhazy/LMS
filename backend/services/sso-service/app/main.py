from __future__ import annotations

from fastapi import FastAPI, HTTPException, Depends
from .security import apply_security_headers, require_jwt

from app.models import CallbackRequest, InitiateSSORequest
from app.service import SSOService

app = FastAPI(title="sso-service", version="0.1.0", dependencies=[Depends(require_jwt)])

apply_security_headers(app)
service = SSOService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "sso-service"}


@app.get("/providers")
def providers() -> dict[str, dict[str, str]]:
    return {"providers_supported": service.provider_matrix()}


@app.post("/sso/initiate")
def initiate_sso(req: InitiateSSORequest):
    try:
        return service.initiate(req)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/sso/callback")
def callback(req: CallbackRequest):
    try:
        return service.callback(req)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
