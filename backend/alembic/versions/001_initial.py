"""Initial migration

Revision ID: 001
Revises:
Create Date: 2026-04-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # agents 表
    op.create_table(
        'agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_builtin', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('persona_system_prompt', sa.Text(), nullable=True),
        sa.Column('persona_expertise', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('thinking_style', sa.String(length=50), nullable=True),
        sa.Column('output_format', sa.Text(), nullable=True),
        sa.Column('output_verbosity', sa.String(length=20), nullable=True),
        sa.Column('visualization_preferences', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('workflow_definition', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )

    # data_sources 表
    op.create_table(
        'data_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('host', sa.String(length=255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('database_name', sa.String(length=100), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('password_encrypted', sa.Text(), nullable=False),
        sa.Column('connection_options', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('schema_cache', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('schema_cache_updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # conversations 表
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('current_context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('context_history', postgresql.ARRAY(postgresql.JSONB(astext_type=sa.Text())), nullable=True),
        sa.Column('is_archived', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['current_agent_id'], ['agents.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # messages 表
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_type', sa.String(length=20), nullable=True),
        sa.Column('execution_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_streaming', sa.Boolean(), nullable=True),
        sa.Column('streaming_completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index('idx_agents_code', 'agents', ['code'])
    op.create_index('idx_agents_builtin', 'agents', ['is_builtin'])
    op.create_index('idx_messages_conversation', 'messages', ['conversation_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('idx_messages_conversation', table_name='messages')
    op.drop_index('idx_agents_builtin', table_name='agents')
    op.drop_index('idx_agents_code', table_name='agents')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('data_sources')
    op.drop_table('agents')
