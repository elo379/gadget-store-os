import importlib
import pkgutil

from alembic import context
from sqlalchemy import UUID, NUMERIC, engine_from_config
from sqlalchemy import pool

from app.core.config import settings
from app.db.base import Base
from app.db.url import database_url_for_environment
import app


config = context.config


def import_model_modules():
    prefixes = (
        ".models",
        ".automation_models",
        ".membership_roles",
        ".store_tree",
        ".invitation_model",
        ".attendance",
        ".branch_assignments",
    )

    for module_info in pkgutil.walk_packages(
        app.__path__,
        app.__name__ + ".",
    ):
        name = module_info.name

        if name.endswith(prefixes):
            importlib.import_module(name)


import_model_modules()


def get_database_url():
    database_url = settings.DATABASE_URL

    if database_url:
        return database_url_for_environment(database_url, settings.ENVIRONMENT)

    return "sqlite:///./alembic_dev.db"


config.set_main_option(
    "sqlalchemy.url",
    get_database_url().replace("%", "%%"),
)

target_metadata = Base.metadata


def compare_type(context, inspected_column, metadata_column, inspected_type, metadata_type):
    # SQLite reflects UUID-backed columns using different storage types
    # depending on SQLAlchemy and the table's creation history. Treat its
    # UUID, NUMERIC and CHAR(32) representations as equivalent so Alembic
    # does not propose meaningless type changes for disposable local DBs.
    if context.dialect.name == "sqlite":
        inspected_name = inspected_type.__class__.__name__.lower()
        metadata_name = metadata_type.__class__.__name__.lower()

        uuid_names = {"uuid"}
        numeric_names = {"numeric", "decimal"}
        inspected_uuid_storage = inspected_name in uuid_names or (
            inspected_name in numeric_names
            or inspected_name == "char" and getattr(inspected_type, "length", None) == 32
        )
        metadata_uuid_storage = metadata_name in uuid_names or (
            metadata_name in numeric_names
            or metadata_name == "char" and getattr(metadata_type, "length", None) == 32
        )

        if inspected_uuid_storage and metadata_uuid_storage:
            return False

    return None


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=compare_type,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {},
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=compare_type,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
