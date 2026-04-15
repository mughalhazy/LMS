"""Service entrypoint."""

from fastapi import Depends, FastAPI

from .security import apply_security_headers, require_jwt

app = FastAPI(title="webhook-service", version="1.0.0", dependencies=[Depends(require_jwt)])

apply_security_headers(app)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "webhook-service"}

@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "webhook-service", "service_up": 1}

