"""create tokens table

Revision ID: 6a4153db949e
Revises: be276ce50fc2
Create Date: 2023-11-16 18:51:54.836630

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a4153db949e'
down_revision: Union[str, None] = 'be276ce50fc2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
    sa.Column('token_type', sa.String(), nullable=False),
    sa.Column('access_token', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tokens_id'), 'tokens', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tokens_id'), table_name='tokens')
    op.drop_table('tokens')
