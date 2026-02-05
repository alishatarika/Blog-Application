from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4ba064b30c8'
down_revision: Union[str, Sequence[str], None] = 'e0fa8cabb49f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.drop_column('otps', 'deleted_at')


def downgrade() -> None:
    op.add_column(
        'otps',
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
    )

