"""add_pgvector_extension

Revision ID: b7c2139e7ba0
Revises: 4daa5abf92d3
Create Date: 2026-04-29 11:22:35.793039

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c2139e7ba0'
down_revision: Union[str, Sequence[str], None] = '4daa5abf92d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector;"))

def downgrade():
    op.execute(sa.text("DROP EXTENSION IF EXISTS vector;"))
