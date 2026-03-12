# User Management Service

FastAPI-based user service implementing:
- user lifecycle
- profile management
- tenant-scoped user isolation
- account status management

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8081
```

## Test

```bash
pytest
```
