"""merge heads

Revision ID: 60b45a5c84f0
Revises: 0235615083f1, 1e8337e5b666
Create Date: 2025-12-03 09:45:23.914416

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60b45a5c84f0'
down_revision: Union[str, Sequence[str], None] = ('0235615083f1', '1e8337e5b666')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
