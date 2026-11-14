"""
KisanRadar Application Package.
Exposes FastAPI application instance for uvicorn app:app execution.
"""
try:
    from app.main import app
except Exception:
    app = None
