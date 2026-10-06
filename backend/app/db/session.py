from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.url import database_url_for_environment


def create_database_engine():
    if not settings.DATABASE_URL:
        return None

    options = {"pool_pre_ping": True}
    # Managed PostgreSQL providers, including Supabase, require encrypted
    # client connections. The same URL policy is used by Alembic.
    database_url = database_url_for_environment(settings.DATABASE_URL, settings.ENVIRONMENT)

    return create_engine(
        database_url,
        **options,
    )


engine = create_database_engine()

SessionLocal = (
    sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )
    if engine is not None
    else None
)


def get_db():
    if SessionLocal is None:
        # Development may intentionally start without a configured database so
        # /health remains available. Database-backed routes must fail as a
        # service configuration error, never as a NoneType call/HTTP 500.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured",
        )

    db: Session = SessionLocal()

    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
