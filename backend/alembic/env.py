"""Explicit schema migrations; importing this environment never seeds domain data."""
from importlib import import_module
from logging.config import fileConfig

from alembic import context

from app.db import Base, engine

if context.config.config_file_name:
    fileConfig(context.config.config_file_name)

for name in ("accounts", "trade", "membership"):
    module = "app.models." + name
    try:
        import_module(module)
    except ModuleNotFoundError as exc:
        if name == "accounts" or exc.name != module:
            raise

target_metadata = Base.metadata

if context.is_offline_mode():
    context.configure(url=engine.url, target_metadata=target_metadata, literal_binds=True,
                      dialect_opts={"paramstyle": "named"}, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True,
                          render_as_batch=engine.dialect.name == "sqlite")
        with context.begin_transaction():
            context.run_migrations()
