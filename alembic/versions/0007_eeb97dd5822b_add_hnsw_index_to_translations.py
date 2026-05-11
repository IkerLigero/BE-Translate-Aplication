"""add_hnsw_index_to_translations

Revision ID: eeb97dd5822b
Revises: 0006_ec4e80e2313e
Create Date: 2026-05-11 12:17:15.844239

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eeb97dd5822b'
down_revision: Union[str, Sequence[str], None] = '0006_ec4e80e2313e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Crear el índice HNSW para búsqueda por coseno
    # Usamos op.execute para enviar el comando nativo de PostgreSQL
    op.execute(
        "CREATE INDEX idx_translations_embedding_hnsw "
        "ON translations USING hnsw (embedding vector_cosine_ops);"
    )


def downgrade() -> None:
    # Para revertir el cambio si algo sale mal
    op.execute("DROP INDEX IF EXISTS idx_translations_embedding_hnsw;")