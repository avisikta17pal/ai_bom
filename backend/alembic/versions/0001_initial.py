from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_admin', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'project',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(), sa.ForeignKey('user.id')),
    )
    op.create_table(
        'projectmember',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('project_id', sa.String(), sa.ForeignKey('project.id')),
        sa.Column('user_id', sa.String(), sa.ForeignKey('user.id')),
        sa.Column('role', sa.String(), nullable=False),
    )
    op.create_table(
        'bom',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('project_id', sa.String(), sa.ForeignKey('project.id')),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(), sa.ForeignKey('user.id')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'bomversion',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('bom_id', sa.String(), sa.ForeignKey('bom.id')),
        sa.Column('version', sa.String(length=64), nullable=False),
        sa.Column('components', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('evaluations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('risk_assessment', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('signatures', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('parent_bom', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'auditlog',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('project_id', sa.String(), sa.ForeignKey('project.id')),
        sa.Column('entity_type', sa.String(length=50)),
        sa.Column('entity_id', sa.String()),
        sa.Column('action', sa.String(length=50)),
        sa.Column('actor_id', sa.String(), sa.ForeignKey('user.id')),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table('auditlog')
    op.drop_table('bomversion')
    op.drop_table('bom')
    op.drop_table('projectmember')
    op.drop_table('project')
    op.drop_table('user')

