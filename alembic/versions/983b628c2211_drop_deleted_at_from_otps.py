"""drop deleted_at from otps

Revision ID: 983b628c2211
Revises: 92ef1fb29bc7
Create Date: 2026-02-05 11:08:23.443513

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '983b628c2211'
down_revision: Union[str, Sequence[str], None] = '92ef1fb29bc7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.drop_column('otps', 'deleted_at')


def downgrade():
    op.add_column(
        'otps',
        sa.Column('deleted_at', sa.DateTime(), nullable=True)
    )
