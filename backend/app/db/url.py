from sqlalchemy.engine import make_url


def database_url_for_environment(database_url: str, environment: str) -> str:
    """Apply the managed PostgreSQL driver and TLS policy for app and Alembic."""
    url = make_url(database_url)
    if (
        environment.strip().lower() in {"staging", "production"}
        and url.get_backend_name() == "postgresql"
    ):
        url = url.set(
            drivername="postgresql+psycopg",
            query={**dict(url.query), "sslmode": "require"},
        )
        return url.render_as_string(hide_password=False)
    return database_url
