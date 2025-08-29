from __future__ import annotations

from alembic import op


revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE OR REPLACE FUNCTION auditlog_append_only()
        RETURNS trigger AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'AuditLog is append-only';
          ELSIF TG_OP = 'UPDATE' THEN
            RAISE EXCEPTION 'AuditLog is append-only';
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS auditlog_guard ON auditlog;
        CREATE TRIGGER auditlog_guard
        BEFORE UPDATE OR DELETE ON auditlog
        FOR EACH ROW EXECUTE PROCEDURE auditlog_append_only();
        """
    )


def downgrade():
    op.execute(
        """
        DROP TRIGGER IF EXISTS auditlog_guard ON auditlog;
        DROP FUNCTION IF EXISTS auditlog_append_only();
        """
    )

