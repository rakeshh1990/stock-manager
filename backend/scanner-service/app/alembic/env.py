from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.database import DATABASE_URL, Base
from app import models  # noqa — ensures ScanResult is registered on Base.metadata

config = context.config
fileConfig(config.config_file_name)

def run_migrations_offline():
    context.configure(url=DATABASE_URL, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        {"sqlalchemy.url": DATABASE_URL},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()