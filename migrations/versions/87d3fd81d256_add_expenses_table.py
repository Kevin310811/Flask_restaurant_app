"""add expenses table

Alembic autogenerate would also have "fixed" FK/index naming drift left
by the earlier hand-written migration b7f2c9ad31e0 (drop/recreate of the
order_items FK, the orders razorpay_order_id index, and missing FK
indexes). Those are no-ops at runtime and touching them risks failure;
this migration is deliberately limited to the new expenses table only.

Revision ID: 87d3fd81d256
Revises: b7f2c9ad31e0
Create Date: 2026-10-24 18:57:54.506791
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '87d3fd81d256'
down_revision = 'b7f2c9ad31e0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('expenses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=30), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('spent_on', sa.Date(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_expenses_category', 'expenses', ['category'], unique=False)
    op.create_index('ix_expenses_spent_on', 'expenses', ['spent_on'], unique=False)


def downgrade():
    op.drop_index('ix_expenses_spent_on', table_name='expenses')
    op.drop_index('ix_expenses_category', table_name='expenses')
    op.drop_table('expenses')
