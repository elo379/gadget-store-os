from fastapi import FastAPI

from app.api import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
    )

    application.include_router(api_router)

    @application.get("/health")
    def health_check():
        return {
            "status": "ok",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }

    return application


app = create_app()
