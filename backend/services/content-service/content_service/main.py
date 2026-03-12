"""Service entrypoint module.

This module documents the HTTP contracts expected for gateway wiring.
It intentionally avoids a framework dependency so it can be embedded into
any Python web runtime (FastAPI, Flask, or internal gateway adapter).
"""

API_ENDPOINTS = [
    {
        "method": "POST",
        "path": "/content/uploads",
        "description": "Upload binary content with metadata for a tenant-scoped learning asset.",
    },
    {
        "method": "PATCH",
        "path": "/content/{content_id}/metadata",
        "description": "Update content metadata and access-policy fields.",
    },
    {
        "method": "GET",
        "path": "/content/{content_id}",
        "description": "Retrieve content metadata and secure delivery reference with access checks.",
    },
    {
        "method": "GET",
        "path": "/content",
        "description": "List tenant-scoped content with optional filters.",
    },
]
