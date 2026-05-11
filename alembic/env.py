import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from dotenv import load_dotenv
import configparser

# 1. Ensure paths are correct to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2. Load environment variables
load_dotenv()

from app.db.base import Base 
target_metadata = Base.metadata

# 3. Alembic Config object
config = context.config

# --- FIX: INI INTERPOLATION & CUSTOM REVISION NAMING ---
if config.config_file_name:
    # Use ConfigParser without interpolation to avoid '%' errors
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(config.config_file_name)

def process_revision_directives(context, revision, directives):
    """Custom directive to prefix revisions with a sequential number (e.g., 0006_hash_name)"""
    if config.get_main_option("revision_environment") == "true":
        return

    # Path to the versions directory
    versions_dir = os.path.join(os.path.dirname(__file__), "versions")
    
    # Count existing .py migration files (excluding __pycache__ and internal files)
    if os.path.exists(versions_dir):
        current_files = [f for f in os.listdir(versions_dir) if f.endswith(".py") and not f.startswith("__")]
        next_num = len(current_files) + 1
    else:
        next_num = 1

    # Apply the prefix to the generated revision ID
    for directive in directives:
        prefix = f"{next_num:04d}"
        # Resulting ID will be 0006_<original_hash>
        directive.rev_id = f"{prefix}_{directive.rev_id}"
# -------------------------------------------------------

# 4. Set database URL from environment
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Logging setup
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=process_revision_directives, # Added custom naming logic
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    """Helper function to run migrations in 'online' mode."""
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        process_revision_directives=process_revision_directives, # Added custom naming logic
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Run migrations in 'online' mode with an async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    try:
        asyncio.run(run_migrations_online())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_migrations_online())