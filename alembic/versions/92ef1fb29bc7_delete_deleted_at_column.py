"""delete deleted_at column

Revision ID: 92ef1fb29bc7
Revises: d1e4b716af4d
Create Date: 2026-02-05 11:05:27.919339

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '92ef1fb29bc7'
down_revision: Union[str, Sequence[str], None] = 'd1e4b716af4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
def upgrade():
    op.drop_column('otps', 'deleted_at')

def downgrade():
    op.add_column(
        'otps',
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
    )

