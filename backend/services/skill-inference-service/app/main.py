"""Service entrypoint."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "skill-inference-service", "service_up": 1}

