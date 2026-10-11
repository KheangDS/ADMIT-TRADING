"""Freeze the initial shared schema without seeding legacy or domain data.

This revision is deliberately independent of application metadata. Future model
changes require a new revision, and downgrade removes only these initial tables.
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # SQLite accepts forward references but cannot ALTER ADD CONSTRAINT.
    # use_alter emits the cyclic FK inline there; PostgreSQL adds it below.
    op.create_table('documents',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('title', sa.String(length=250), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('language', sa.String(length=4), nullable=False),
    sa.Column('filename', sa.String(length=250), nullable=False),
    sa.Column('content_type', sa.String(length=150), nullable=False),
    sa.Column('size_bytes', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=10), nullable=False),
    sa.Column('publication_id', sa.String(length=36), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('storage_name', sa.String(length=100), nullable=False),
    sa.Column('preview_name', sa.String(length=100), nullable=True),
    sa.Column('preview_status', sa.String(length=15), nullable=False),
    sa.CheckConstraint("language IN ('en','km','both')", name='document_language'),
    sa.CheckConstraint("preview_status IN ('ready','unavailable','pending','failed')", name='document_preview_status'),
    sa.CheckConstraint("status IN ('draft','published')", name='document_status'),
    sa.CheckConstraint('size_bytes > 0', name='document_positive_size'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_status'), 'documents', ['status'], unique=False)
    op.create_table('membership_plans',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('duration_unit', sa.String(length=5), nullable=False),
    sa.Column('duration_count', sa.Integer(), nullable=False),
    sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.CheckConstraint("currency != 'KHR' OR amount = CAST(amount AS BIGINT)", name='plan_whole_riel'),
    sa.CheckConstraint("currency IN ('USD','KHR')", name='plan_currency'),
    sa.CheckConstraint("duration_unit IN ('month','year') AND duration_count > 0", name='plan_duration'),
    sa.CheckConstraint('display_order >= 0', name='plan_display_order'),
    sa.CheckConstraint('amount > 0', name='plan_positive_amount'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('oauth_states',
    sa.Column('state_hash', sa.String(length=64), nullable=False),
    sa.Column('browser_hash', sa.String(length=64), nullable=False),
    sa.Column('nonce', sa.String(length=128), nullable=False),
    sa.Column('pkce_verifier', sa.String(length=128), nullable=False),
    sa.Column('return_to', sa.String(length=2048), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('state_hash')
    )
    op.create_index(op.f('ix_oauth_states_expires_at'), 'oauth_states', ['expires_at'], unique=False)
    op.create_table('outbox_jobs',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('kind', sa.String(length=40), nullable=False),
    sa.Column('entity_id', sa.String(length=36), nullable=False),
    sa.Column('dedupe_key', sa.String(length=150), nullable=False),
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=15), nullable=False),
    sa.Column('attempts', sa.Integer(), nullable=False),
    sa.Column('available_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
    sa.Column('lock_token', sa.String(length=36), nullable=True),
    sa.Column('last_error', sa.String(length=80), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("status IN ('pending','processing','done','failed')", name='outbox_status'),
    sa.CheckConstraint('attempts >= 0', name='outbox_attempts'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('dedupe_key')
    )
    op.create_index(op.f('ix_outbox_jobs_available_at'), 'outbox_jobs', ['available_at'], unique=False)
    op.create_index(op.f('ix_outbox_jobs_status'), 'outbox_jobs', ['status'], unique=False)
    op.create_table('trade_imports',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('storage_name', sa.String(length=80), nullable=True),
    sa.Column('raw_payload', sa.Text(), nullable=True),
    sa.Column('mode', sa.String(length=10), nullable=False),
    sa.Column('status', sa.String(length=12), nullable=False),
    sa.Column('start_month', sa.String(length=7), nullable=True),
    sa.Column('end_month', sa.String(length=7), nullable=True),
    sa.Column('rows', sa.JSON(), nullable=False),
    sa.Column('errors', sa.JSON(), nullable=False),
    sa.Column('duplicate_count', sa.Integer(), nullable=False),
    sa.Column('column_mapping', sa.JSON(), nullable=False),
    sa.Column('preview', sa.JSON(), nullable=False),
    sa.Column('base_revision_id', sa.String(length=36), nullable=True),
    sa.Column('registry_generation', sa.Integer(), nullable=False),
    sa.Column('revision_id', sa.String(length=36), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("mode IN ('complete','partial')"),
    sa.CheckConstraint("status IN ('staged','invalid','committed')"),
    sa.ForeignKeyConstraint(['revision_id'], ['trade_revisions.id'], name='fk_trade_import_revision', use_alter=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('trade_registry',
    sa.Column('kind', sa.String(length=10), nullable=False),
    sa.Column('code', sa.String(length=160), nullable=False),
    sa.Column('name_en', sa.String(length=300), nullable=False),
    sa.Column('name_km', sa.String(length=300), nullable=False),
    sa.Column('parent_code', sa.String(length=4), nullable=True),
    sa.Column('iso3', sa.String(length=3), nullable=True),
    sa.Column('aliases', sa.JSON(), nullable=False),
    sa.CheckConstraint("kind IN ('hs4','hs8','country')"),
    sa.PrimaryKeyConstraint('kind', 'code')
    )
    op.create_table('users',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('google_sub', sa.String(length=255), nullable=True),
    sa.Column('email', sa.String(length=320), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=True),
    sa.Column('role', sa.String(length=16), nullable=False),
    sa.Column('disabled', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("role IN ('member', 'admin', 'superadmin')", name='ck_user_role'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('google_sub')
    )
    op.create_table('audit_events',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('actor_id', sa.String(length=36), nullable=True),
    sa.Column('action', sa.String(length=128), nullable=False),
    sa.Column('entity_type', sa.String(length=128), nullable=False),
    sa.Column('entity_id', sa.String(length=255), nullable=False),
    sa.Column('details', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_events_actor_id'), 'audit_events', ['actor_id'], unique=False)
    op.create_index(op.f('ix_audit_events_created_at'), 'audit_events', ['created_at'], unique=False)
    op.create_table('auth_sessions',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('role_at_issue', sa.String(length=16), nullable=False),
    sa.Column('csrf_token', sa.String(length=128), nullable=False),
    sa.Column('access_token', sa.Text(), nullable=False),
    sa.Column('access_expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('rotated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_auth_sessions_expires_at'), 'auth_sessions', ['expires_at'], unique=False)
    op.create_index(op.f('ix_auth_sessions_user_id'), 'auth_sessions', ['user_id'], unique=False)
    op.create_table('memberships',
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked', sa.Boolean(), nullable=False),
    sa.Column('source', sa.String(length=30), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('payment_requests',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('user_name', sa.String(length=250), nullable=False),
    sa.Column('user_email', sa.String(length=320), nullable=False),
    sa.Column('plan_id', sa.String(length=36), nullable=False),
    sa.Column('plan_name', sa.String(length=200), nullable=False),
    sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('duration_unit', sa.String(length=5), nullable=False),
    sa.Column('duration_count', sa.Integer(), nullable=False),
    sa.Column('payer_name', sa.String(length=250), nullable=False),
    sa.Column('status', sa.String(length=15), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('bank_reference', sa.String(length=200), nullable=True),
    sa.Column('rejection_reason', sa.Text(), nullable=True),
    sa.Column('checkout_ip', sa.String(length=64), nullable=True),
    sa.Column('device_type', sa.String(length=20), nullable=False),
    sa.Column('user_agent', sa.String(length=1000), nullable=False),
    sa.Column('qr_url', sa.Text(), nullable=False),
    sa.Column('delayed_reported_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("amount > 0 AND currency IN ('USD','KHR')", name='payment_amount_currency'),
    sa.CheckConstraint("currency != 'KHR' OR amount = CAST(amount AS BIGINT)", name='payment_whole_riel'),
    sa.CheckConstraint("duration_unit IN ('month','year') AND duration_count > 0", name='payment_duration'),
    sa.CheckConstraint("status IN ('created','submitted','approved','rejected','cancelled')", name='payment_status'),
    sa.ForeignKeyConstraint(['plan_id'], ['membership_plans.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('bank_reference')
    )
    op.create_index(op.f('ix_payment_requests_status'), 'payment_requests', ['status'], unique=False)
    op.create_index(op.f('ix_payment_requests_user_id'), 'payment_requests', ['user_id'], unique=False)
    op.create_table('trade_revisions',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('source_import_id', sa.String(length=36), nullable=False),
    sa.Column('row_count', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=10), nullable=False),
    sa.Column('registry_snapshot', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['source_import_id'], ['trade_imports.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('source_import_id')
    )
    op.create_table('receipts',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('payment_id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('number', sa.String(length=50), nullable=False),
    sa.Column('user_name', sa.String(length=250), nullable=False),
    sa.Column('user_email', sa.String(length=320), nullable=False),
    sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('paid_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('approved_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('pdf_status', sa.String(length=10), nullable=False),
    sa.Column('email_status', sa.String(length=10), nullable=False),
    sa.Column('storage_name', sa.String(length=100), nullable=True),
    sa.CheckConstraint("email_status IN ('pending','sent','failed')", name='receipt_email_status'),
    sa.CheckConstraint("pdf_status IN ('pending','ready','failed')", name='receipt_pdf_status'),
    sa.ForeignKeyConstraint(['payment_id'], ['payment_requests.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('number'),
    sa.UniqueConstraint('payment_id')
    )
    op.create_index(op.f('ix_receipts_user_id'), 'receipts', ['user_id'], unique=False)
    op.create_table('session_credentials',
    sa.Column('secret_hash', sa.String(length=64), nullable=False),
    sa.Column('session_id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('spent_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['auth_sessions.id'], ),
    sa.PrimaryKeyConstraint('secret_hash')
    )
    op.create_index(op.f('ix_session_credentials_session_id'), 'session_credentials', ['session_id'], unique=False)
    op.create_table('trade_publications',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('revision_id', sa.String(length=36), nullable=False),
    sa.Column('start_month', sa.String(length=7), nullable=False),
    sa.Column('end_month', sa.String(length=7), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('start_month <= end_month'),
    sa.ForeignKeyConstraint(['revision_id'], ['trade_revisions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('trade_rows',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('revision_id', sa.String(length=36), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('month', sa.Integer(), nullable=False),
    sa.Column('hs4_code', sa.String(length=4), nullable=False),
    sa.Column('hs8_code', sa.String(length=8), nullable=False),
    sa.Column('country_code', sa.String(length=160), nullable=False),
    sa.Column('weight_kg', sa.Numeric(precision=24, scale=6), nullable=False),
    sa.Column('val_khr', sa.Numeric(precision=24, scale=6), nullable=False),
    sa.Column('source_import_id', sa.String(length=36), nullable=False),
    sa.Column('source_row', sa.Integer(), nullable=False),
    sa.CheckConstraint('month BETWEEN 1 AND 12'),
    sa.CheckConstraint('weight_kg >= 0 AND val_khr >= 0'),
    sa.CheckConstraint('year BETWEEN 1900 AND 2200'),
    sa.ForeignKeyConstraint(['revision_id'], ['trade_revisions.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('revision_id', 'year', 'month', 'hs8_code', 'country_code')
    )
    op.create_index(op.f('ix_trade_rows_revision_id'), 'trade_rows', ['revision_id'], unique=False)
    op.create_table('trade_head',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('revision_id', sa.String(length=36), nullable=True),
    sa.Column('publication_id', sa.String(length=36), nullable=True),
    sa.Column('generation', sa.Integer(), nullable=False),
    sa.Column('registry_generation', sa.Integer(), nullable=False),
    sa.CheckConstraint('id = 1'),
    sa.ForeignKeyConstraint(['publication_id'], ['trade_publications.id'], ),
    sa.ForeignKeyConstraint(['revision_id'], ['trade_revisions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    if op.get_context().dialect.name != "sqlite":
        op.create_foreign_key(
            "fk_trade_import_revision", "trade_imports", "trade_revisions",
            ["revision_id"], ["id"],
        )


def downgrade():
    if op.get_context().dialect.name == "sqlite":
        # Break the populated import/revision cycle before dropping revisions.
        # This also works in offline SQL with foreign-key enforcement enabled.
        op.execute("UPDATE trade_imports SET revision_id = NULL")
    else:
        op.drop_constraint("fk_trade_import_revision", "trade_imports", type_="foreignkey")
    op.drop_table("trade_head")
    op.drop_table("trade_rows")
    op.drop_table("trade_publications")
    op.drop_table("session_credentials")
    op.drop_table("receipts")
    op.drop_table("trade_revisions")
    op.drop_table("payment_requests")
    op.drop_table("memberships")
    op.drop_table("auth_sessions")
    op.drop_table("audit_events")
    op.drop_table("users")
    op.drop_table("trade_registry")
    op.drop_table("trade_imports")
    op.drop_table("outbox_jobs")
    op.drop_table("oauth_states")
    op.drop_table("membership_plans")
    op.drop_table("documents")
