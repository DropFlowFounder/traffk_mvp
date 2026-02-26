"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE userrole AS ENUM ('advertiser', 'traffic', 'both')")
    op.execute("CREATE TYPE taskstatus AS ENUM ('draft', 'published', 'taken', 'submitted', 'completed', 'cancelled', 'disputed')")
    op.execute("CREATE TYPE transactiontype AS ENUM ('deposit', 'payout', 'commission', 'refund')")
    op.execute("CREATE TYPE transactionstatus AS ENUM ('pending', 'confirmed', 'rejected')")
    op.execute("CREATE TYPE disputestatus AS ENUM ('open', 'resolved')")
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('role', postgresql.ENUM('advertiser', 'traffic', 'both', name='userrole'), nullable=True),
        sa.Column('balance', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('reputation', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id')
    )
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)
    
    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('advertiser_id', sa.BigInteger(), nullable=False),
        sa.Column('executor_id', sa.BigInteger(), nullable=True),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('link', sa.String(length=500), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('deadline_days', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('draft', 'published', 'taken', 'submitted', 'completed', 'cancelled', 'disputed', name='taskstatus'), nullable=False),
        sa.Column('proof_text', sa.Text(), nullable=True),
        sa.Column('proof_photos', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('taken_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['advertiser_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['executor_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('task_id', sa.BigInteger(), nullable=True),
        sa.Column('type', postgresql.ENUM('deposit', 'payout', 'commission', 'refund', name='transactiontype'), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'confirmed', 'rejected', name='transactionstatus'), nullable=False),
        sa.Column('admin_comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create disputes table
    op.create_table(
        'disputes',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('task_id', sa.BigInteger(), nullable=False),
        sa.Column('opened_by', sa.BigInteger(), nullable=False),
        sa.Column('resolved_by', sa.BigInteger(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', postgresql.ENUM('open', 'resolved', name='disputestatus'), nullable=False),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['opened_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('task_id')
    )


def downgrade() -> None:
    op.drop_table('disputes')
    op.drop_table('transactions')
    op.drop_table('tasks')
    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.drop_table('users')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS disputestatus")
    op.execute("DROP TYPE IF EXISTS transactionstatus")
    op.execute("DROP TYPE IF EXISTS transactiontype")
    op.execute("DROP TYPE IF EXISTS taskstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
