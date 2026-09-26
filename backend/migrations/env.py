import importlib
import pkgutil

from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from app.core.config import settings
from app.db.base import Base
import app


config = context.config


def import_model_modules():
    prefixes = (
        ".models",
        ".membership_roles",
        ".store_tree",
        ".invitation_model",
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
        return database_url

    return "sqlite:///./alembic_dev.db"


config.set_main_option(
    "sqlalchemy.url",
    get_database_url(),
)

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
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
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
