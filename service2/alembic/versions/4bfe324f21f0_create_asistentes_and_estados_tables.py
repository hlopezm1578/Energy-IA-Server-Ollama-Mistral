"""Create Asistentes and Estados tables

Revision ID: 4bfe324f21f0
Revises: 39d2d6fd5346
Create Date: 2024-10-18 07:42:23.577976

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4bfe324f21f0'
down_revision: Union[str, None] = '39d2d6fd5346'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Estados',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nombre', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_Estados_id'), 'Estados', ['id'], unique=False)
    op.add_column('Asistentes', sa.Column('chunks', sa.Integer(), nullable=False))
    op.add_column('Asistentes', sa.Column('overlap', sa.Integer(), nullable=False))
    op.add_column('Asistentes', sa.Column('estado_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'Asistentes', 'Estados', ['estado_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'Asistentes', type_='foreignkey')
    op.drop_column('Asistentes', 'estado_id')
    op.drop_column('Asistentes', 'overlap')
    op.drop_column('Asistentes', 'chunks')
    op.drop_index(op.f('ix_Estados_id'), table_name='Estados')
    op.drop_table('Estados')
    # ### end Alembic commands ###
