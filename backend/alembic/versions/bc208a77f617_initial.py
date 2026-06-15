"""initial

Revision ID: bc208a77f617
Revises:
Create Date: 2026-06-10 19:34:19.542363
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc208a77f617'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # sessions table
    op.create_table('sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.String(length=36), nullable=True),
    sa.Column('vision', sa.Text(), nullable=True),
    sa.Column('mission', sa.Text(), nullable=True),
    sa.Column('values', sa.JSON(), nullable=True),
    sa.Column('company_name', sa.String(length=200), nullable=True),
    sa.Column('industry', sa.String(length=100), nullable=True),
    sa.Column('stage', sa.String(length=20), nullable=True),
    sa.Column('team_size', sa.String(length=20), nullable=True),
    sa.Column('selected_track', sa.Text(), nullable=True),
    sa.Column('additional_info', sa.Text(), nullable=True),
    sa.Column('current_stage', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sessions_id'), 'sessions', ['id'], unique=False)
    op.create_index(op.f('ix_sessions_session_id'), 'sessions', ['session_id'], unique=True)

    # messages table
    op.create_table('messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.Integer(), nullable=True),
    sa.Column('role', sa.String(length=20), nullable=True),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('stage', sa.Integer(), nullable=True),
    sa.Column('extra_data', sa.JSON(), nullable=True),
    sa.Column('file_content', sa.Text(), nullable=True),
    sa.Column('file_name', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)

    # reports table
    op.create_table('reports',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.Integer(), nullable=True),
    sa.Column('report_type', sa.String(length=50), nullable=True),
    sa.Column('title', sa.String(length=200), nullable=True),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('sources', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_id'), 'reports', ['id'], unique=False)

    # report_tasks table
    op.create_table('report_tasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('task_id', sa.String(length=100), nullable=True),
    sa.Column('session_db_id', sa.Integer(), nullable=True),
    sa.Column('report_type', sa.String(length=50), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('progress', sa.Integer(), nullable=True),
    sa.Column('message', sa.String(length=500), nullable=True),
    sa.Column('report_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(length=200), nullable=True),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('sources', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_report_tasks_id'), 'report_tasks', ['id'], unique=False)
    op.create_index(op.f('ix_report_tasks_task_id'), 'report_tasks', ['task_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_report_tasks_task_id'), table_name='report_tasks')
    op.drop_index(op.f('ix_report_tasks_id'), table_name='report_tasks')
    op.drop_table('report_tasks')

    op.drop_index(op.f('ix_reports_id'), table_name='reports')
    op.drop_table('reports')

    op.drop_index(op.f('ix_messages_id'), table_name='messages')
    op.drop_table('messages')

    op.drop_index(op.f('ix_sessions_session_id'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_id'), table_name='sessions')
    op.drop_table('sessions')
