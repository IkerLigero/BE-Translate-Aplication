import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from dotenv import load_dotenv

# 1. Añadimos la raíz del proyecto al path para que encuentre el módulo 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2. Cargamos variables de entorno desde el .env
load_dotenv()

# 3. Importamos la Base que tiene todos los modelos cargados
# Asegúrate de haber creado app/db/base.py con las importaciones de User y Translation
from app.db.base import Base 
target_metadata = Base.metadata

# Este es el objeto de configuración de Alembic
config = context.config

# 4. Forzamos a Alembic a usar la URL de la base de datos de nuestro .env
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Configuración de logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def run_migrations_offline() -> None:
    """Modo offline: genera scripts SQL sin conectarse a la DB."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    """Función auxiliar síncrona para ejecutar las migraciones."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Modo online: para motores asíncronos como asyncpg."""
    
    # Creamos la configuración para el motor asíncrono
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Ejecutamos la migración síncrona dentro del contexto asíncrono
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    # 5. Ejecutamos el loop de asyncio para la conexión online
    try:
        asyncio.run(run_migrations_online())
    except RuntimeError:
        # En caso de que ya exista un event loop activo
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_migrations_online())