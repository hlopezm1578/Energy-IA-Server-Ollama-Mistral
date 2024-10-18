"""Remove test column from Asistentes

Revision ID: 39d2d6fd5346
Revises: b25906a3eb21
Create Date: 2024-10-17 10:39:56.146029

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39d2d6fd5346'
down_revision: Union[str, None] = 'b25906a3eb21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Asistentes', 'test')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Asistentes', sa.Column('test', sa.VARCHAR(), autoincrement=False, nullable=False))
    # ### end Alembic commands ###
