from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
import logging
import json
import re
import time
import uuid
from datetime import datetime, timezone

from app.api.router import api_router
from app.core.config import settings
from app.db.session import engine

logger = logging.getLogger("gsos.http")


class JsonLogFormatter(logging.Formatter):
    def format(self, record):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("method", "path", "request_id", "status_code", "duration_ms"):
            if hasattr(record, key):
                entry[key] = getattr(record, key)
        return json.dumps(entry, separators=(",", ":"))


if not logging.getLogger().handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        *settings.cors_origin_list,
    ],
    allow_origin_regex=(r"https://.*\.app\.github\.dev" if settings.ENVIRONMENT == "development" else None),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/ready", include_in_schema=False)
def readiness():
    if engine is None:
        return JSONResponse({"status": "not_ready", "checks": {"database": "not_configured"}}, status_code=503)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            migration = connection.execute(
                text("SELECT version_num FROM alembic_version LIMIT 1")
            ).scalar_one_or_none()
            if migration is None:
                raise RuntimeError("database migrations have not been applied")
    except Exception:
        logger.error("readiness database check failed")
        return JSONResponse({"status": "not_ready", "checks": {"database": "unavailable"}}, status_code=503)
    return {"status": "ready", "checks": {"database": "ok", "migrations": "applied"}}


@app.middleware("http")
async def structured_request_log(request, call_next):
    started = time.perf_counter()
    supplied_id = request.headers.get("x-request-id", "")
    request_id = supplied_id if re.fullmatch(r"[A-Za-z0-9._-]{1,64}", supplied_id) else str(uuid.uuid4())
    response = await call_next(request)
    route = request.scope.get("route")
    route_template = getattr(route, "path", None) or "/unmatched"
    logger.info(
        "http_request",
        extra={"method": request.method, "path": route_template, "request_id": request_id,
               "status_code": response.status_code, "duration_ms": round((time.perf_counter() - started) * 1000, 2)},
    )
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(self), microphone=(), geolocation=()"
    return response
