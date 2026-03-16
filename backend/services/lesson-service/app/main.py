"""Service entrypoint."""

from fastapi import Depends, FastAPI

from .security import apply_security_headers, require_jwt

app = FastAPI(title="lesson-service", version="1.0.0", dependencies=[Depends(require_jwt)])

apply_security_headers(app)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "lesson-service"}
