"""Initial auth schema and tables

Revision ID: 001
Revises: 
Create Date: 2024-01-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from uuid import uuid4

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

# Default tenant for self-hosted mode
DEFAULT_TENANT_ID = '00000000-0000-0000-0000-000000000000'
DEFAULT_TENANT_NAME = 'Default'
DEFAULT_TENANT_SLUG = 'default'


def upgrade() -> None:
    """Create auth schema and initial tables with RLS."""
    
    # Create auth schema
    op.execute("CREATE SCHEMA IF NOT EXISTS auth")
    
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid4),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(63), nullable=False),
        sa.Column('settings', sa.Text(), nullable=True, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
        schema='auth'
    )
    op.create_index('ix_auth_tenants_slug', 'tenants', ['slug'], schema='auth')
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid4),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(63), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['auth.tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'email', name='uq_tenant_email'),
        schema='auth'
    )
    op.create_index('ix_auth_users_tenant_id', 'users', ['tenant_id'], schema='auth')
    op.create_index('ix_auth_users_tenant_id_email', 'users', ['tenant_id', 'email'], schema='auth')
    
    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid4),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('key_hash', sa.String(255), nullable=False),
        sa.Column('prefix', sa.String(10), nullable=False),
        sa.Column('scopes', sa.Text(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['auth.tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['auth.users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash'),
        sa.CheckConstraint('expires_at > created_at', name='ck_expires_after_created'),
        schema='auth'
    )
    op.create_index('ix_auth_api_keys_key_hash', 'api_keys', ['key_hash'], schema='auth')
    op.create_index('ix_auth_api_keys_tenant_id', 'api_keys', ['tenant_id'], schema='auth')
    op.create_index('ix_auth_api_keys_tenant_id_user_id', 'api_keys', ['tenant_id', 'user_id'], schema='auth')
    op.create_index('ix_auth_api_keys_expires_at', 'api_keys', ['expires_at'], schema='auth')
    
    # Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False),
        sa.Column('device_info', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['auth.users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
        schema='auth'
    )
    op.create_index('ix_auth_refresh_tokens_token_hash', 'refresh_tokens', ['token_hash'], schema='auth')
    op.create_index('ix_auth_refresh_tokens_user_id', 'refresh_tokens', ['user_id'], schema='auth')
    op.create_index('ix_auth_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'], schema='auth')
    
    # Create contexts table with tenant_id
    op.create_table(
        'contexts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid4),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('namespace', sa.String(255), nullable=False),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('value', postgresql.JSONB(), nullable=False),
        sa.Column('tags', postgresql.JSONB(), nullable=True, default=[]),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['auth.tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['auth.users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['auth.users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'namespace', 'key', name='uq_tenant_namespace_key')
    )
    op.create_index('ix_contexts_tenant_id', 'contexts', ['tenant_id'])
    op.create_index('ix_contexts_tenant_id_namespace', 'contexts', ['tenant_id', 'namespace'])
    op.create_index('ix_contexts_tenant_id_created_at', 'contexts', ['tenant_id', 'created_at'])
    op.create_index('ix_contexts_tags', 'contexts', ['tags'], postgresql_using='gin')
    
    # Create memories table with tenant_id
    op.create_table(
        'memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid4),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, default={}),
        sa.Column('similarity_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['auth.tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['auth.users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_memories_tenant_id', 'memories', ['tenant_id'])
    op.create_index('ix_memories_tenant_id_created_at', 'memories', ['tenant_id', 'created_at'])
    op.create_index('ix_memories_metadata', 'memories', ['metadata'], postgresql_using='gin')
    
    # Enable Row-Level Security
    op.execute("ALTER TABLE contexts ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE memories ENABLE ROW LEVEL SECURITY")
    
    # Create RLS policies for contexts
    op.execute("""
        CREATE POLICY tenant_isolation_contexts ON contexts
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
        WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid)
    """)
    
    # Create RLS policies for memories
    op.execute("""
        CREATE POLICY tenant_isolation_memories ON memories
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
        WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid)
    """)
    
    # Insert default tenant for self-hosted mode
    op.execute(f"""
        INSERT INTO auth.tenants (id, name, slug, settings, is_active)
        VALUES (
            '{DEFAULT_TENANT_ID}'::uuid,
            '{DEFAULT_TENANT_NAME}',
            '{DEFAULT_TENANT_SLUG}',
            '{{"type": "self-hosted", "features": {{"multi_tenant": false}}}}',
            true
        )
    """)


def downgrade() -> None:
    """Drop all tables and schema."""
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS tenant_isolation_contexts ON contexts")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_memories ON memories")
    
    # Drop tables
    op.drop_table('memories')
    op.drop_table('contexts')
    op.drop_table('refresh_tokens', schema='auth')
    op.drop_table('api_keys', schema='auth')
    op.drop_table('users', schema='auth')
    op.drop_table('tenants', schema='auth')
    
    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS auth CASCADE")