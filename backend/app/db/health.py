from sqlalchemy import text

from app.db.session import engine


def check_database_connection() -> bool:
    if engine is None:
        return False

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return True
