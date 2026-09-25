from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def create_database_engine():
    if not settings.DATABASE_URL:
        return None

    return create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
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
        raise RuntimeError("DATABASE_URL is not configured")

    db: Session = SessionLocal()

    try:
        yield db
    finally:
        db.close()
