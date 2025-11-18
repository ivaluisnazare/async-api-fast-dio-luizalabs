from alembic import op
import sqlalchemy as sa

revision = '422ecada4fca'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('accounts',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('balance', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
                    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'),
                              nullable=True),
                    sa.PrimaryKeyConstraint('id', name=op.f('pk_accounts'))
                    )

    op.create_index(op.f('ix_accounts_user_id'), 'accounts', ['user_id'], unique=False)

    op.execute("COMMENT ON TABLE accounts IS 'Stores user account information and balances'")


def downgrade() -> None:
    op.drop_index(op.f('ix_accounts_user_id'), table_name='accounts')

    op.drop_table('accounts')